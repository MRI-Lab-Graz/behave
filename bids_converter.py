"""
BIDS converter module for BEHAVE.

This module contains the core conversion logic for transforming behavioral data
from Excel format into BIDS-compliant JSON and TSV files.
"""

import os
import json
import logging
import math
import re
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from pathlib import Path

from config import BehaveConfig, ColumnNames, BIDSPaths, DEFAULT_CONFIG
from excel_handler import (
    load_and_validate_excel, load_session_file, load_demographics_file,
    load_variables_file, normalize_item_name, clean_text_data, convert_data_types
)
from validators import (
    validate_subject_id, validate_session_id, validate_task_name,
    validate_data_consistency, validate_json_structure, validate_participants_data,
    sanitize_for_tsv
)

logger = logging.getLogger(__name__)


class BIDSConverter:
    """Main class for converting behavioral data to BIDS format."""
    
    def __init__(self, config: BehaveConfig = DEFAULT_CONFIG):
        self.config = config
    
    def convert_excel_to_json(self, excel_file: str, output_json_file: str, 
                            anonymize: bool = False) -> None:
        """
        Convert Excel file to BIDS-compliant JSON.
        
        Args:
            excel_file: Path to input Excel file
            output_json_file: Path to output JSON file
            anonymize: Whether to anonymize item descriptions
        """
        logger.info(f"Converting Excel to JSON: {excel_file} -> {output_json_file}")
        
        # Load and validate Excel file
        excel_data = load_and_validate_excel(excel_file, self.config)
        
        # Process main sheet
        json_data = self._process_main_sheet(excel_data['main'], anonymize)
        
        # Process metadata sheets
        metadata = self._process_metadata_sheets(
            excel_data['task_desc'], 
            excel_data['nonlikert']
        )
        json_data.update(metadata)
        
        # Validate JSON structure
        validate_json_structure(json_data, excel_file)
        
        # Write JSON file
        self._write_json_file(json_data, output_json_file)
        
        logger.info(f"Successfully converted {excel_file} to JSON")
    
    def _process_main_sheet(self, df_main: pd.DataFrame, anonymize: bool) -> Dict[str, Any]:
        """
        Process the main sheet of the Excel file to extract survey item information.
        
        Args:
            df_main: DataFrame containing the main sheet data
            anonymize: Whether to anonymize item descriptions
            
        Returns:
            Dictionary with cleaned and structured survey item data
        """
        json_data = {}
        
        for idx, row in df_main.iterrows():
            item_key = self._get_item_key(row)
            if not item_key:
                continue
            
            # Create entry
            entry = self._create_item_entry(row, idx, anonymize)
            
            # Clean the key and add to data
            clean_key = re.sub(r'[-_]', '', item_key)
            json_data[clean_key] = entry
        
        return json_data
    
    def _get_item_key(self, row: pd.Series) -> Optional[str]:
        """Extract and validate item key from row."""
        item_key = row.get(ColumnNames.ITEM_NAME, 'Unknown Item')
        
        if pd.isna(item_key):
            return None
        
        item_key = str(item_key).strip()
        
        # Skip header rows or invalid entries
        if item_key.lower().startswith("itemname") or item_key == 'Unknown Item':
            return None
        
        return item_key
    
    def _create_item_entry(self, row: pd.Series, idx: int, anonymize: bool) -> Dict[str, Any]:
        """Create a BIDS-compliant entry for a survey item."""
        # Handle anonymization
        if anonymize:
            description = f"Question {idx + 1}"
        else:
            description = row.get(ColumnNames.ITEM_DESCRIPTION, 'No description available')
        
        entry = {"Description": str(description)}
        
        # Handle Likert scale levels
        self._add_likert_levels(entry, row)
        
        # Handle units for non-Likert items
        self._add_units(entry, row)
        
        return entry
    
    def _add_likert_levels(self, entry: Dict[str, Any], row: pd.Series) -> None:
        """Add Likert scale levels to item entry."""
        try:
            num_levels = int(row[ColumnNames.LIKERT_SCALE]) if pd.notna(row[ColumnNames.LIKERT_SCALE]) else 0
        except (ValueError, KeyError, TypeError):
            num_levels = 0
        
        if num_levels <= 0:
            return
        
        levels = {}
        for i in range(num_levels):
            level_col = f'levels.{i}' if i > 0 else 'levels'
            description_col = f'leveldescription.{i}' if i > 0 else 'leveldescription'
            
            if (level_col in row.index and description_col in row.index and
                pd.notna(row[level_col]) and pd.notna(row[description_col])):
                
                try:
                    level_value = int(row[level_col])
                    level_description = str(row[description_col])
                    levels[str(level_value)] = level_description
                except (ValueError, TypeError):
                    continue
        
        if levels:
            entry["Levels"] = levels
    
    def _add_units(self, entry: Dict[str, Any], row: pd.Series) -> None:
        """Add units for non-Likert items."""
        if "Levels" in entry:
            return  # Already has levels, skip units
        
        if (ColumnNames.LEVEL_DESCRIPTION in row.index and 
            pd.notna(row[ColumnNames.LEVEL_DESCRIPTION])):
            entry["Units"] = str(row[ColumnNames.LEVEL_DESCRIPTION]).strip()
    
    def _process_metadata_sheets(self, df_task_desc: pd.DataFrame, 
                               df_nonlikert: pd.DataFrame) -> Dict[str, Any]:
        """
        Process metadata sheets to extract additional information.
        
        Args:
            df_task_desc: Task description DataFrame
            df_nonlikert: Non-Likert items DataFrame
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Process both metadata sheets
        for df in [df_task_desc, df_nonlikert]:
            for _, row in df.iterrows():
                key = row.get(ColumnNames.KEY_NAME)
                value = row.get(ColumnNames.DESCRIPTION_META, '')
                
                if pd.notna(key) and pd.notna(value):
                    metadata[str(key)] = str(value)
        
        return metadata
    
    def _write_json_file(self, json_data: Dict[str, Any], output_file: str) -> None:
        """Write JSON data to file with proper formatting."""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        
        logger.debug(f"JSON data written to {output_file}")
    
    def create_bids_structure(self, session_file: str, task_name: str, task_file: str,
                            output_folder: str) -> None:
        """
        Create BIDS structure and convert session data to TSV files.
        
        Args:
            session_file: Path to session Excel file
            task_name: Name of the task
            task_file: Path to task definition file
            output_folder: Output folder for BIDS structure
        """
        logger.debug(f"Creating BIDS structure for {session_file}, task: {task_name}")
        
        # Load and prepare session data
        df_session = load_session_file(session_file)
        df_session = self._prepare_session_data(df_session)
        
        # Load task definition
        task_data = load_and_validate_excel(task_file, self.config)
        task_items = self._extract_task_items(task_data['main'])
        
        # Validate data consistency
        validation_results = validate_data_consistency(df_session, task_items, task_name)
        self._log_validation_results(validation_results, task_name)
        
        # Filter relevant columns
        relevant_columns = ['subject_id', 'session'] + [
            col for col in df_session.columns 
            if task_name.upper() in col.upper() and col in task_items
        ]
        
        if len(relevant_columns) <= 2:
            logger.warning(f"No relevant data found for task {task_name} in {session_file}")
            return
        
        df_filtered = df_session[relevant_columns]
        
        # Process each subject/session
        for _, row in df_filtered.iterrows():
            self._process_subject_session(row, task_name, output_folder)
    
    def _prepare_session_data(self, df_session: pd.DataFrame) -> pd.DataFrame:
        """Prepare session data by normalizing columns and IDs."""
        # Normalize column names
        df_session.columns = [normalize_item_name(col) for col in df_session.columns]
        
        # Rename standard columns
        column_mapping = {}
        for col in df_session.columns:
            if col.lower() == 'id':
                column_mapping[col] = 'subject_id'
            elif col.lower() == 'ses':
                column_mapping[col] = 'session'
        
        if column_mapping:
            df_session = df_session.rename(columns=column_mapping)
        
        # Validate required columns exist
        required_cols = ['subject_id', 'session']
        missing_cols = [col for col in required_cols if col not in df_session.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in session file: {missing_cols}")
        
        return df_session
    
    def _extract_task_items(self, df_main: pd.DataFrame) -> List[str]:
        """Extract and normalize task item names from task definition."""
        task_items = []
        
        for item in df_main[ColumnNames.ITEM_NAME]:
            if pd.isna(item) or 'example' in str(item).lower():
                continue
            
            normalized_item = normalize_item_name(str(item))
            task_items.append(normalized_item)
        
        return task_items
    
    def _log_validation_results(self, results: Dict[str, Any], task_name: str) -> None:
        """Log validation results with appropriate levels."""
        if results['missing_items']:
            logger.warning(f"Task {task_name}: Missing items: {results['missing_items']}")
        
        if results['extra_columns']:
            logger.debug(f"Task {task_name}: Extra columns: {results['extra_columns']}")
        
        if results['nan_values']:
            logger.info(f"Task {task_name}: Columns with NaN values: {results['nan_values']}")
    
    def _process_subject_session(self, row: pd.Series, task_name: str, 
                               output_folder: str) -> None:
        """Process a single subject/session combination."""
        # Validate and normalize IDs
        subject_id = validate_subject_id(row['subject_id'])
        session = validate_session_id(row['session'])
        
        logger.debug(f"Processing {subject_id}, session {session}")
        
        # Create output directory
        session_path = BIDSPaths.get_subject_session_path(subject_id, session)
        output_dir = os.path.join(output_folder, session_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare output file
        filename = BIDSPaths.get_task_tsv_filename(subject_id, session, task_name)
        output_file = os.path.join(output_dir, filename)
        
        # Convert row to DataFrame and clean data
        row_df = pd.DataFrame([row])
        row_df = self._clean_row_data(row_df)
        
        # Remove ID columns (not needed in TSV)
        row_df = row_df.drop(columns=['subject_id', 'session'], errors='ignore')
        
        # Save as TSV
        row_df.to_csv(output_file, sep='\t', index=False)
        logger.debug(f"Saved TSV: {output_file}")
    
    def _clean_row_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean row data for TSV output."""
        df_clean = df.copy()
        
        # Convert floats to integers where possible
        for col in df_clean.columns:
            if df_clean[col].dtype.kind in 'fi':  # float or integer
                df_clean[col] = df_clean[col].map(
                    lambda x: int(x) if isinstance(x, float) and x.is_integer() else x
                )
        
        # Clean text data
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].map(clean_text_data)
        
        return df_clean
    
    def convert_demographics_to_participants(self, demographics_file: str, 
                                           variables_file: str, output_folder: str) -> None:
        """
        Convert demographics data to BIDS participants files.
        
        Args:
            demographics_file: Path to demographics Excel file
            variables_file: Path to variables definition file
            output_folder: Output folder for BIDS files
        """
        logger.info("Converting demographics to participants files")
        
        # Load data
        df_demo = load_demographics_file(demographics_file)
        df_variables, dataset_description = load_variables_file(variables_file)
        
        # Validate participants data
        validation_results = validate_participants_data(df_demo, df_variables)
        self._log_participants_validation(validation_results)
        
        # Prepare participants DataFrame
        df_participants = self._prepare_participants_data(df_demo, df_variables)
        
        # Write participants.tsv
        participants_tsv = os.path.join(output_folder, BIDSPaths.PARTICIPANTS_TSV)
        self._write_participants_tsv(df_participants, participants_tsv)
        
        # Write participants.json
        participants_json = os.path.join(output_folder, BIDSPaths.PARTICIPANTS_JSON)
        self._write_participants_json(df_variables, participants_json)
        
        # Write dataset_description.json
        dataset_json = os.path.join(output_folder, BIDSPaths.DATASET_DESCRIPTION_JSON)
        self._write_dataset_description(dataset_description, dataset_json)
        
        logger.info("Successfully created participants files")
    
    def _prepare_participants_data(self, df_demo: pd.DataFrame, 
                                 df_variables: pd.DataFrame) -> pd.DataFrame:
        """Prepare participants DataFrame with proper data types and normalization."""
        # Get required columns
        required_columns = df_variables[ColumnNames.VARIABLE_NAME].tolist()
        
        # Add missing columns
        missing_columns = [col for col in required_columns if col not in df_demo.columns]
        for col in missing_columns:
            df_demo[col] = self.config.missing_value_replacement
            logger.warning(f"Added missing column '{col}' with default value")
        
        # Extract participants data
        df_participants = df_demo[required_columns].copy()
        
        # Normalize participant IDs
        if 'id' in df_participants.columns:
            df_participants['participant_id'] = df_participants['id'].apply(validate_subject_id)
            df_participants = df_participants.drop(columns=['id'])
            
            # Move participant_id to first column
            cols = df_participants.columns.tolist()
            cols.insert(0, cols.pop(cols.index('participant_id')))
            df_participants = df_participants[cols]
        
        # Convert data types
        dtype_map = dict(zip(df_variables[ColumnNames.VARIABLE_NAME], 
                           df_variables[ColumnNames.DATA_TYPE].str.lower()))
        df_participants = convert_data_types(df_participants, dtype_map, self.config)
        
        # Handle missing values
        df_participants = df_participants.replace(self.config.missing_value_code, pd.NA)
        
        return df_participants
    
    def _log_participants_validation(self, results: Dict[str, Any]) -> None:
        """Log participants validation results."""
        for warning in results['warnings']:
            logger.warning(warning)
        
        if results['type_mismatches']:
            for col, expected, actual in results['type_mismatches']:
                logger.warning(f"Type mismatch for {col}: expected {expected}, got {actual}")
    
    def _write_participants_tsv(self, df_participants: pd.DataFrame, output_file: str) -> None:
        """Write participants.tsv file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Sanitize data for TSV
        df_clean = df_participants.copy()
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].map(sanitize_for_tsv)
        
        df_clean.to_csv(output_file, sep='\t', index=False, na_rep='n/a')
        logger.info(f"✅ Saved participants.tsv: {output_file}")
    
    def _write_participants_json(self, df_variables: pd.DataFrame, output_file: str) -> None:
        """Write participants.json file."""
        participants_json = {}
        
        for _, row in df_variables.iterrows():
            variable_name = str(row[ColumnNames.VARIABLE_NAME]).lower()
            
            if variable_name == 'id':
                continue  # Skip ID column
            
            entry = {"Description": str(row.get(ColumnNames.DESCRIPTION, ''))}
            
            # Add levels for categorical variables
            data_type = str(row.get(ColumnNames.DATA_TYPE, '')).lower()
            levels_str = row.get(ColumnNames.LEVELS, '')
            
            if data_type in ['cat_num', 'cat_string'] and pd.notna(levels_str):
                levels = self._parse_levels_string(str(levels_str))
                if levels:
                    entry["Levels"] = levels
            
            participants_json[variable_name] = entry
        
        # Add participant_id metadata
        participants_json['participant_id'] = {
            "Description": "Unique participant identifier",
            "LongName": "Participant ID"
        }
        
        self._write_json_file(participants_json, output_file)
        logger.info(f"✅ Saved participants.json: {output_file}")
    
    def _parse_levels_string(self, levels_str: str) -> Dict[str, str]:
        """Parse levels string into dictionary."""
        levels = {}
        
        for level in levels_str.split(';'):
            key_value = level.strip().split(':')
            if len(key_value) == 2:
                key, val = key_value
                levels[key.strip()] = val.strip()
        
        return levels
    
    def _write_dataset_description(self, dataset_description: Dict[str, Any], 
                                 output_file: str) -> None:
        """Write dataset_description.json file."""
        if not dataset_description:
            # Create minimal dataset description
            dataset_description = {
                "Name": "BEHAVE Converted Dataset",
                "BIDSVersion": self.config.bids_version
            }
        else:
            # Process special BIDS fields
            dataset_description = self._process_dataset_description(dataset_description)
        
        # Validate and complete dataset description
        dataset_description = self._validate_dataset_description(dataset_description)
        
        self._write_json_file(dataset_description, output_file)
        logger.info(f"✅ Saved dataset_description.json: {output_file}")
    
    def _process_dataset_description(self, dataset_desc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process dataset description to handle special BIDS fields.
        
        Args:
            dataset_desc: Raw dataset description from Excel
            
        Returns:
            Processed dataset description with proper BIDS formatting
        """
        processed = {}
        
        for key, value in dataset_desc.items():
            # Convert to string and strip whitespace
            key = str(key).strip()
            value = str(value).strip() if pd.notna(value) else ""
            
            # Handle special fields
            if key.lower() == 'authors':
                processed[key] = self._process_authors_field(value)
            elif key.lower() in ['referencesandlinks', 'referencesandlink']:
                # Handle References and Links as array
                processed['ReferencesAndLinks'] = self._process_array_field(value)
            elif key.lower() in ['fundingsources', 'funding']:
                # Handle Funding as array
                processed['Funding'] = self._process_array_field(value)
            elif key.lower() == 'license':
                # Handle license field (common typo: Licence vs License)
                processed['License'] = value
            elif key.lower() == 'licence':
                # Handle common typo
                processed['License'] = value
            else:
                # Standard fields - keep as string
                processed[key] = value
        
        return processed
    
    def _process_authors_field(self, authors_str: str) -> List[str]:
        """
        Process Authors field to convert string to array.
        
        Args:
            authors_str: String with authors (semicolon or comma separated)
            
        Returns:
            List of author names
        """
        if not authors_str:
            return []
        
        # Try semicolon first, then comma
        if ';' in authors_str:
            authors = [author.strip() for author in authors_str.split(';')]
        elif ',' in authors_str:
            authors = [author.strip() for author in authors_str.split(',')]
        else:
            # Single author
            authors = [authors_str.strip()]
        
        # Remove empty entries
        authors = [author for author in authors if author]
        
        return authors
    
    def _process_array_field(self, field_str: str) -> List[str]:
        """
        Process array fields (like ReferencesAndLinks, Funding).
        
        Args:
            field_str: String with array items (semicolon or comma separated)
            
        Returns:
            List of items
        """
        if not field_str:
            return []
        
        # Try semicolon first, then comma
        if ';' in field_str:
            items = [item.strip() for item in field_str.split(';')]
        elif ',' in field_str:
            items = [item.strip() for item in field_str.split(',')]
        else:
            # Single item
            items = [field_str.strip()]
        
        # Remove empty entries
        items = [item for item in items if item]
        
        return items
    
    def _validate_dataset_description(self, dataset_desc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and ensure required BIDS fields are present in dataset description.
        
        Args:
            dataset_desc: Dataset description dictionary
            
        Returns:
            Validated and completed dataset description
        """
        # Required BIDS fields
        required_fields = {
            'Name': 'Unnamed Dataset',
            'BIDSVersion': self.config.bids_version,
            'DatasetType': 'raw'
        }
        
        # Ensure required fields are present
        for field, default_value in required_fields.items():
            if field not in dataset_desc or not dataset_desc[field]:
                logger.warning(f"Missing required field '{field}', using default: {default_value}")
                dataset_desc[field] = default_value
        
        # Validate BIDSVersion format
        bids_version = dataset_desc.get('BIDSVersion', '')
        if not re.match(r'^\d+\.\d+\.\d+$', bids_version):
            logger.warning(f"Invalid BIDSVersion format: {bids_version}. Using default: {self.config.bids_version}")
            dataset_desc['BIDSVersion'] = self.config.bids_version
        
        # Validate DatasetType
        valid_types = ['raw', 'derivative']
        if dataset_desc.get('DatasetType') not in valid_types:
            logger.warning(f"Invalid DatasetType. Using 'raw'")
            dataset_desc['DatasetType'] = 'raw'
        
        return dataset_desc


def cleanup_unused_json_files(output_folder: str) -> None:
    """
    Remove task JSON files that don't have corresponding TSV files.
    
    Args:
        output_folder: BIDS output folder
    """
    logger.info("🔍 Cleaning up unused task JSON files...")
    
    # Find all task JSON files
    json_pattern = os.path.join(output_folder, "task-*_beh.json")
    import glob
    task_json_files = glob.glob(json_pattern)
    
    removed_count = 0
    
    for task_json in task_json_files:
        # Extract task name
        task_name = Path(task_json).name.replace("task-", "").replace("_beh.json", "")
        
        # Search for matching TSV files
        tsv_pattern = os.path.join(output_folder, "**", f"*task-{task_name}_beh.tsv")
        matching_tsv_files = glob.glob(tsv_pattern, recursive=True)
        
        if not matching_tsv_files:
            logger.info(f"🗑️ Removing unused JSON: {task_json}")
            os.remove(task_json)
            removed_count += 1
        else:
            logger.debug(f"✅ Keeping JSON for task {task_name} ({len(matching_tsv_files)} TSV files)")
    
    logger.info(f"✅ Cleanup completed. Removed {removed_count} unused JSON files.")
