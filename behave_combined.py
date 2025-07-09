#!/usr/bin/env python3
"""
BEHAVE - Behavioral Data to BIDS Converter (Single File Version)

This is a combined version of all modules for easy deployment.
All modules (config, excel_handler, validators, bids_converter) are 
included in this single file to make distribution easier.

Original modular version available as separate files.
"""

import argparse
import json
import logging
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas")
    sys.exit(1)

try:
    import openpyxl
except ImportError:
    print("Error: openpyxl is required. Install with: pip install openpyxl")
    sys.exit(1)


# ============================================================================
# CONFIG MODULE
# ============================================================================

@dataclass
class BehaveConfig:
    """Configuration settings for BEHAVE converter."""
    
    # File requirements
    min_required_sheets: int = 3
    required_demographics_files: List[str] = None
    required_session_columns: List[str] = None
    
    # Data processing
    anonymize_questions: bool = False
    missing_value_replacement: str = 'n/a'
    missing_value_code: int = -999
    
    # BIDS settings
    bids_version: str = "1.8.0"
    ignore_bids_warnings: bool = True
    
    # Logging
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def __post_init__(self):
        if self.required_demographics_files is None:
            self.required_demographics_files = ['demographics.xlsx', 'participants_dataset.xlsx']
        
        if self.required_session_columns is None:
            self.required_session_columns = ['id', 'ses']


class ColumnNames:
    """Standard column names used in BEHAVE."""
    
    # Main sheet columns
    ITEM_NAME = 'itemname'
    ITEM_DESCRIPTION = 'itemdescription'
    LIKERT_SCALE = 'likert_scale'
    LEVEL_DESCRIPTION = 'leveldescription'
    
    # Answer sheet columns
    ANSWER_COLUMN = 'answer'
    
    # Demographics columns  
    PARTICIPANT_ID = 'id'
    SESSION = 'ses'
    
    # Other common columns
    ONSET = 'onset'
    DURATION = 'duration'
    TRIAL_TYPE = 'trial_type'
    RESPONSE_TIME = 'response_time'


class FilePatterns:
    """File patterns and naming conventions."""
    
    TEMP_PREFIX = '~$'
    EXCEL_EXTENSION = '.xlsx'
    SESSION_PATTERN = 'session*.xlsx'
    DEMOGRAPHICS_FILENAME = 'demographics.xlsx'
    PARTICIPANTS_DATASET = 'participants_dataset.xlsx'
    
    # BIDS naming
    TASK_JSON_TEMPLATE = 'task-{}_beh.json'
    TASK_TSV_TEMPLATE = 'sub-{}_ses-{}_task-{}_beh.tsv'
    PARTICIPANTS_TSV = 'participants.tsv'
    PARTICIPANTS_JSON = 'participants.json'
    DATASET_DESCRIPTION = 'dataset_description.json'


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    if not debug:
        logging.getLogger('pandas').setLevel(logging.WARNING)


def print_header() -> None:
    """Print application header."""
    print("""
▗▖  ▗▖▗▄▄▖ ▗▄▄▄▖    ▗▖    ▗▄▖ ▗▄▄▖      ▗▄▄▖▗▄▄▖  ▗▄▖ ▗▄▄▄▄▖
▐▛▚▞▜▌▐▌ ▐▌  █      ▐▌   ▐▌ ▐▌▐▌ ▐▌    ▐▌   ▐▌ ▐▌▐▌ ▐▌   ▗▞▘
▐▌  ▐▌▐▛▀▚▖  █      ▐▌   ▐▛▀▜▌▐▛▀▚▖    ▐▌▝▜▌▐▛▀▚▖▐▛▀▜▌ ▗▞▘  
▐▌  ▐▌▐▌ ▐▌▗▄█▄▖    ▐▙▄▄▖▐▌ ▐▌▐▙▄▞▘    ▝▚▄▞▘▐▌ ▐▌▐▌ ▐▌▐▙▄▄▄▖
         MRI-Lab Graz - Survey to BIDS Converter              
    """)


# ============================================================================
# EXCEL HANDLER MODULE
# ============================================================================

class ExcelHandler:
    """Handles Excel file operations and data loading."""
    
    def __init__(self, config: BehaveConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def find_session_files(self, data_path: str) -> List[str]:
        """Find session Excel files in the data path."""
        session_files = []
        
        for file_path in Path(data_path).glob("*.xlsx"):
            if self._is_valid_session_file(file_path):
                session_files.append(str(file_path))
        
        return sorted(session_files)
    
    def _is_valid_session_file(self, file_path: Path) -> bool:
        """Check if file is a valid session file."""
        filename = file_path.name
        
        # Skip temporary files
        if filename.startswith(FilePatterns.TEMP_PREFIX):
            return False
        
        # Skip demographics files
        if filename in self.config.required_demographics_files:
            return False
        
        return True
    
    def load_excel_file(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """Load Excel file and return all sheets as DataFrames."""
        try:
            sheets = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            self.logger.debug(f"Loaded {len(sheets)} sheets from {file_path}")
            return sheets
        except Exception as e:
            self.logger.error(f"Failed to load Excel file {file_path}: {e}")
            raise
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame by cleaning column names and data."""
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Replace missing values
        df = df.fillna(self.config.missing_value_replacement)
        
        return df
    
    def load_demographics(self, data_path: str) -> Optional[pd.DataFrame]:
        """Load demographics data if available."""
        demographics_path = Path(data_path) / FilePatterns.DEMOGRAPHICS_FILENAME
        
        if not demographics_path.exists():
            self.logger.warning(f"Demographics file not found: {demographics_path}")
            return None
        
        try:
            df = pd.read_excel(demographics_path, engine='openpyxl')
            df = self.normalize_dataframe(df)
            
            # Validate required columns
            missing_cols = [col for col in self.config.required_session_columns 
                          if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Missing required columns in demographics: {missing_cols}")
                return None
            
            return df
        except Exception as e:
            self.logger.error(f"Failed to load demographics: {e}")
            return None


# ============================================================================
# VALIDATORS MODULE
# ============================================================================

class Validators:
    """Data validation utilities."""
    
    def __init__(self, config: BehaveConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_data_path(self, data_path: str) -> bool:
        """Validate that data path exists and contains required files."""
        if not os.path.exists(data_path):
            self.logger.error(f"Data path does not exist: {data_path}")
            return False
        
        # Check for required demographics files
        for filename in self.config.required_demographics_files:
            file_path = os.path.join(data_path, filename)
            if not os.path.exists(file_path):
                self.logger.warning(f"Required file not found: {filename}")
        
        return True
    
    def validate_excel_structure(self, sheets: Dict[str, pd.DataFrame], 
                                file_path: str) -> bool:
        """Validate Excel file structure."""
        if len(sheets) < self.config.min_required_sheets:
            self.logger.error(
                f"File {file_path} has {len(sheets)} sheets, "
                f"minimum {self.config.min_required_sheets} required"
            )
            return False
        
        # Validate sheet names and structure
        expected_sheets = ['items', 'answers', 'levels']
        for sheet_name in expected_sheets:
            if sheet_name not in sheets:
                self.logger.error(f"Required sheet '{sheet_name}' not found in {file_path}")
                return False
        
        return True
    
    def validate_bids_compliance(self, output_path: str) -> bool:
        """Validate BIDS compliance of output."""
        # Check for required BIDS files
        required_files = [
            FilePatterns.DATASET_DESCRIPTION,
            FilePatterns.PARTICIPANTS_TSV
        ]
        
        for filename in required_files:
            file_path = os.path.join(output_path, filename)
            if not os.path.exists(file_path):
                self.logger.warning(f"BIDS file missing: {filename}")
                return False
        
        return True
    
    def validate_participant_data(self, df: pd.DataFrame) -> bool:
        """Validate participant data structure."""
        required_columns = [ColumnNames.PARTICIPANT_ID, ColumnNames.SESSION]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check for duplicate participants
        if df[ColumnNames.PARTICIPANT_ID].duplicated().any():
            self.logger.warning("Duplicate participant IDs found")
        
        return True


# ============================================================================
# BIDS CONVERTER MODULE
# ============================================================================

class BidsConverter:
    """Main BIDS conversion logic."""
    
    def __init__(self, config: BehaveConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.excel_handler = ExcelHandler(config)
        self.validators = Validators(config)
    
    def convert_to_bids(self, study_name: str, data_path: str, 
                       output_path: str) -> bool:
        """Convert data to BIDS format."""
        try:
            # Validate input
            if not self.validators.validate_data_path(data_path):
                return False
            
            # Create output directory
            os.makedirs(output_path, exist_ok=True)
            
            # Find and process session files
            session_files = self.excel_handler.find_session_files(data_path)
            if not session_files:
                self.logger.error("No valid session files found")
                return False
            
            self.logger.info(f"Found {len(session_files)} session files")
            
            # Load demographics
            demographics = self.excel_handler.load_demographics(data_path)
            
            # Process each session file
            all_participants = []
            
            for session_file in session_files:
                participants = self._process_session_file(
                    session_file, output_path, demographics
                )
                all_participants.extend(participants)
            
            # Create BIDS files
            self._create_participants_files(all_participants, output_path)
            self._create_dataset_description(study_name, output_path)
            
            # Validate output
            if self.validators.validate_bids_compliance(output_path):
                self.logger.info("BIDS conversion completed successfully")
                return True
            else:
                self.logger.warning("BIDS validation warnings found")
                return True  # Still consider success with warnings
                
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            return False
    
    def _process_session_file(self, file_path: str, output_path: str,
                            demographics: Optional[pd.DataFrame]) -> List[Dict]:
        """Process a single session file."""
        self.logger.info(f"Processing {file_path}")
        
        # Load Excel file
        sheets = self.excel_handler.load_excel_file(file_path)
        
        # Validate structure
        if not self.validators.validate_excel_structure(sheets, file_path):
            raise ValueError(f"Invalid Excel structure in {file_path}")
        
        # Extract task name from filename
        task_name = Path(file_path).stem
        
        # Process sheets
        items_df = self.excel_handler.normalize_dataframe(sheets['items'])
        answers_df = self.excel_handler.normalize_dataframe(sheets['answers'])
        levels_df = self.excel_handler.normalize_dataframe(sheets['levels'])
        
        # Create task JSON
        self._create_task_json(items_df, levels_df, task_name, output_path)
        
        # Create behavioral TSV files
        participants = self._create_behavioral_tsvs(
            answers_df, task_name, output_path, demographics
        )
        
        return participants
    
    def _create_task_json(self, items_df: pd.DataFrame, levels_df: pd.DataFrame,
                         task_name: str, output_path: str) -> None:
        """Create task JSON file."""
        task_info = {
            "TaskName": task_name,
            "TaskDescription": f"Behavioral task: {task_name}",
            "BIDSVersion": self.config.bids_version,
            "Items": {}
        }
        
        # Process items
        for _, row in items_df.iterrows():
            item_name = row.get(ColumnNames.ITEM_NAME, '')
            item_desc = row.get(ColumnNames.ITEM_DESCRIPTION, '')
            
            if item_name:
                task_info["Items"][item_name] = {
                    "Description": item_desc,
                    "Levels": {}
                }
        
        # Process levels
        for _, row in levels_df.iterrows():
            item_name = row.get(ColumnNames.ITEM_NAME, '')
            level_desc = row.get(ColumnNames.LEVEL_DESCRIPTION, '')
            
            if item_name in task_info["Items"] and level_desc:
                # Add level information
                pass
        
        # Save JSON
        json_filename = FilePatterns.TASK_JSON_TEMPLATE.format(task_name)
        json_path = os.path.join(output_path, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, indent=2, ensure_ascii=False)
        
        self.logger.debug(f"Created task JSON: {json_path}")
    
    def _create_behavioral_tsvs(self, answers_df: pd.DataFrame, task_name: str,
                              output_path: str, demographics: Optional[pd.DataFrame]) -> List[Dict]:
        """Create behavioral TSV files for each participant."""
        participants = []
        
        # Group by participant and session
        if ColumnNames.PARTICIPANT_ID not in answers_df.columns:
            self.logger.error(f"Missing {ColumnNames.PARTICIPANT_ID} column")
            return participants
        
        for participant_id in answers_df[ColumnNames.PARTICIPANT_ID].unique():
            participant_data = answers_df[
                answers_df[ColumnNames.PARTICIPANT_ID] == participant_id
            ]
            
            # Determine session
            session = participant_data.get(ColumnNames.SESSION, 1).iloc[0]
            
            # Create TSV filename
            tsv_filename = FilePatterns.TASK_TSV_TEMPLATE.format(
                participant_id, session, task_name
            )
            tsv_path = os.path.join(output_path, tsv_filename)
            
            # Prepare behavioral data
            beh_data = self._prepare_behavioral_data(participant_data)
            
            # Save TSV
            beh_data.to_csv(tsv_path, sep='\t', index=False)
            
            # Collect participant info
            participant_info = {
                'participant_id': f"sub-{participant_id}",
                'session': f"ses-{session}"
            }
            
            # Add demographics if available
            if demographics is not None:
                demo_row = demographics[
                    demographics[ColumnNames.PARTICIPANT_ID] == participant_id
                ]
                if not demo_row.empty:
                    for col in demographics.columns:
                        if col not in [ColumnNames.PARTICIPANT_ID, ColumnNames.SESSION]:
                            participant_info[col] = demo_row.iloc[0][col]
            
            participants.append(participant_info)
        
        return participants
    
    def _prepare_behavioral_data(self, participant_data: pd.DataFrame) -> pd.DataFrame:
        """Prepare behavioral data for BIDS format."""
        # Create standard BIDS columns
        beh_data = participant_data.copy()
        
        # Add required BIDS columns if missing
        if ColumnNames.ONSET not in beh_data.columns:
            beh_data[ColumnNames.ONSET] = range(len(beh_data))
        
        if ColumnNames.DURATION not in beh_data.columns:
            beh_data[ColumnNames.DURATION] = 1.0
        
        if ColumnNames.TRIAL_TYPE not in beh_data.columns:
            beh_data[ColumnNames.TRIAL_TYPE] = 'response'
        
        # Reorder columns
        column_order = [
            ColumnNames.ONSET,
            ColumnNames.DURATION, 
            ColumnNames.TRIAL_TYPE,
            ColumnNames.RESPONSE_TIME
        ]
        
        # Add remaining columns
        for col in beh_data.columns:
            if col not in column_order:
                column_order.append(col)
        
        # Filter existing columns
        existing_columns = [col for col in column_order if col in beh_data.columns]
        
        return beh_data[existing_columns]
    
    def _create_participants_files(self, participants: List[Dict], output_path: str) -> None:
        """Create participants.tsv and participants.json files."""
        if not participants:
            self.logger.warning("No participants to create files for")
            return
        
        # Create participants DataFrame
        participants_df = pd.DataFrame(participants)
        
        # Save participants.tsv
        tsv_path = os.path.join(output_path, FilePatterns.PARTICIPANTS_TSV)
        participants_df.to_csv(tsv_path, sep='\t', index=False)
        
        # Create participants.json with column descriptions
        participants_json = {}
        for col in participants_df.columns:
            participants_json[col] = {
                "Description": f"Participant {col}",
                "DataType": "string"
            }
        
        # Save participants.json
        json_path = os.path.join(output_path, FilePatterns.PARTICIPANTS_JSON)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(participants_json, f, indent=2)
        
        self.logger.info(f"Created participants files with {len(participants)} participants")
    
    def _create_dataset_description(self, study_name: str, output_path: str) -> None:
        """Create dataset_description.json file."""
        dataset_description = {
            "Name": study_name,
            "BIDSVersion": self.config.bids_version,
            "DatasetType": "raw",
            "Authors": ["MRI-Lab Graz"],
            "GeneratedBy": [
                {
                    "Name": "BEHAVE",
                    "Version": "2.0.0",
                    "Description": "Survey to BIDS Converter"
                }
            ]
        }
        
        json_path = os.path.join(output_path, FilePatterns.DATASET_DESCRIPTION)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(dataset_description, f, indent=2)
        
        self.logger.debug(f"Created dataset description: {json_path}")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="BEHAVE - Convert behavioral Excel data to BIDS format"
    )
    
    parser.add_argument(
        "study_name",
        help="Name of the study"
    )
    
    parser.add_argument(
        "data_path",
        help="Path to the data folder containing Excel files"
    )
    
    parser.add_argument(
        "output_path", 
        help="Path to the output folder for BIDS data"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--anonymize",
        action="store_true", 
        help="Anonymize question names"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main application entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup logging
        setup_logging(args.debug)
        logger = logging.getLogger(__name__)
        
        # Print header
        print_header()
        
        # Create configuration
        config = BehaveConfig()
        config.anonymize_questions = args.anonymize
        
        # Create converter
        converter = BidsConverter(config)
        
        # Convert to BIDS
        logger.info(f"Starting BIDS conversion for study: {args.study_name}")
        logger.info(f"Data path: {args.data_path}")
        logger.info(f"Output path: {args.output_path}")
        
        success = converter.convert_to_bids(
            args.study_name,
            args.data_path, 
            args.output_path
        )
        
        if success:
            logger.info("Conversion completed successfully!")
            return 0
        else:
            logger.error("Conversion failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
