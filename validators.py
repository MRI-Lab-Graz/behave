"""
Data validation module for BEHAVE.

This module provides validation functions for ensuring data integrity
and BIDS compliance throughout the conversion process.
"""

import os
import re
import logging
import subprocess
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path

from config import BehaveConfig, ColumnNames, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


def validate_subject_id(subject_id: str) -> str:
    """
    Validate and normalize a subject ID to BIDS format.
    
    Args:
        subject_id: Raw subject ID
        
    Returns:
        Normalized subject ID in BIDS format (sub-XXX)
    """
    if pd.isna(subject_id):
        return "sub-unknown"
    
    subject_id = str(subject_id).strip()
    
    # Remove multiple 'sub-' prefixes
    subject_id = re.sub(r"^sub-+", "sub-", subject_id)
    
    # Add 'sub-' prefix if missing
    if not subject_id.startswith("sub-"):
        # Handle numeric IDs
        if re.match(r"^\d+$", subject_id):
            subject_id = f"sub-{subject_id.zfill(3)}"
        else:
            subject_id = f"sub-{subject_id}"
    
    # Validate BIDS compliance
    if not re.match(r"^sub-[a-zA-Z0-9]+$", subject_id):
        logger.warning(f"Subject ID may not be BIDS compliant: {subject_id}")
    
    return subject_id


def validate_session_id(session_id: str) -> str:
    """
    Validate and normalize a session ID.
    
    Args:
        session_id: Raw session ID
        
    Returns:
        Normalized session ID
    """
    if pd.isna(session_id):
        return "01"
    
    session_id = str(session_id).strip()
    
    # Ensure it's numeric and zero-padded
    if session_id.isdigit():
        return session_id.zfill(2)
    
    return session_id


def validate_task_name(task_name: str) -> str:
    """
    Validate and normalize a task name for BIDS compliance.
    
    Args:
        task_name: Raw task name
        
    Returns:
        BIDS-compliant task name
    """
    if pd.isna(task_name):
        raise ValidationError("Task name cannot be empty")
    
    task_name = str(task_name).strip()
    
    # Remove file extension if present
    task_name = re.sub(r'\.(xlsx?|csv)$', '', task_name, flags=re.IGNORECASE)
    
    # Replace problematic characters with underscores
    task_name = re.sub(r'[^a-zA-Z0-9]', '', task_name)
    
    if not task_name:
        raise ValidationError("Task name is empty after normalization")
    
    return task_name.lower()


def validate_folder_structure(data_folder: str, resources_folder: str, 
                            config: BehaveConfig = DEFAULT_CONFIG) -> None:
    """
    Validate that required folders and files exist.
    
    Args:
        data_folder: Path to data folder
        resources_folder: Path to resources folder
        config: Configuration object
        
    Raises:
        ValidationError: If required folders/files are missing
    """
    # Check folders exist
    if not os.path.exists(data_folder):
        raise ValidationError(f"Data folder does not exist: {data_folder}")
    
    if not os.path.exists(resources_folder):
        raise ValidationError(f"Resources folder does not exist: {resources_folder}")
    
    # Check required files in data folder
    for required_file in config.required_demographics_files:
        file_path = os.path.join(data_folder, required_file)
        if not os.path.exists(file_path):
            raise ValidationError(f"Required file missing in data folder: {required_file}")
    
    logger.info("Folder structure validation passed")


def validate_dataframe_not_empty(df: pd.DataFrame, context: str) -> None:
    """
    Validate that a DataFrame is not empty.
    
    Args:
        df: DataFrame to check
        context: Context for error message
        
    Raises:
        ValidationError: If DataFrame is empty
    """
    if df.empty:
        raise ValidationError(f"DataFrame is empty: {context}")
    
    if df.shape[0] == 0:
        raise ValidationError(f"DataFrame has no rows: {context}")


def validate_required_columns(df: pd.DataFrame, required_columns: List[str], 
                            context: str) -> None:
    """
    Validate that DataFrame contains required columns.
    
    Args:
        df: DataFrame to check
        required_columns: List of required column names
        context: Context for error message
        
    Raises:
        ValidationError: If required columns are missing
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValidationError(f"Missing required columns in {context}: {missing_columns}")


def validate_no_duplicate_subjects(df: pd.DataFrame, subject_col: str = 'participant_id') -> None:
    """
    Validate that there are no duplicate subjects in the data.
    
    Args:
        df: DataFrame to check
        subject_col: Name of the subject ID column
        
    Raises:
        ValidationError: If duplicate subjects are found
    """
    if subject_col not in df.columns:
        logger.warning(f"Cannot validate duplicates: column '{subject_col}' not found")
        return
    
    duplicates = df[df[subject_col].duplicated()]
    if not duplicates.empty:
        duplicate_ids = duplicates[subject_col].tolist()
        raise ValidationError(f"Duplicate subject IDs found: {duplicate_ids}")


def validate_data_consistency(session_data: pd.DataFrame, task_items: List[str], 
                            task_name: str) -> Dict[str, Any]:
    """
    Validate data consistency between session data and task definitions.
    
    Args:
        session_data: DataFrame with session data
        task_items: List of expected task items
        task_name: Name of the task
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'missing_items': [],
        'extra_columns': [],
        'nan_values': {},
        'warnings': []
    }
    
    # Find task-related columns in session data
    task_columns = [col for col in session_data.columns if task_name.upper() in col.upper()]
    
    # Check for missing task items
    missing_items = [item for item in task_items if item not in task_columns]
    results['missing_items'] = missing_items
    
    if missing_items:
        results['warnings'].append(f"Missing task items for {task_name}: {missing_items}")
    
    # Check for extra columns
    extra_columns = [col for col in task_columns if col not in task_items]
    results['extra_columns'] = extra_columns
    
    if extra_columns:
        results['warnings'].append(f"Extra columns found for {task_name}: {extra_columns}")
    
    # Check for NaN values in task columns
    for col in task_columns:
        if col in session_data.columns:
            nan_count = session_data[col].isna().sum()
            if nan_count > 0:
                results['nan_values'][col] = nan_count
    
    return results


def validate_json_structure(json_data: Dict[str, Any], context: str = "") -> None:
    """
    Validate JSON structure for BIDS compliance.
    
    Args:
        json_data: JSON data to validate
        context: Context for error messages
        
    Raises:
        ValidationError: If JSON structure is invalid
    """
    if not isinstance(json_data, dict):
        raise ValidationError(f"JSON data must be a dictionary: {context}")
    
    if not json_data:
        raise ValidationError(f"JSON data is empty: {context}")
    
    # Check for required BIDS fields in behavioral data
    required_fields = ['Description']
    for key, value in json_data.items():
        if isinstance(value, dict) and 'Description' not in value:
            logger.warning(f"Missing 'Description' field for item '{key}' in {context}")


def validate_bids_structure(output_folder: str) -> bool:
    """
    Run the BIDS Validator using Deno to validate the output structure.
    
    Args:
        output_folder: Path to the BIDS output folder
        
    Returns:
        True if validation passes, False otherwise
    """
    if not os.path.exists(output_folder):
        logger.error(f"BIDS directory does not exist: {output_folder}")
        return False
    
    logger.info("🚀 Running BIDS Validator...")
    
    # Construct the validation command
    validator_command = [
        "deno", "run", "-ERN", "jsr:@bids/validator",
        output_folder, "--ignoreWarnings", "-v"
    ]
    
    try:
        # Combine stdout and stderr
        result = subprocess.run(
            validator_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        logger.info("✅ BIDS validation completed successfully!")
        logger.debug(result.stdout)
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("❌ BIDS validation timed out!")
        return False
        
    except subprocess.CalledProcessError as e:
        logger.error("❌ BIDS validation failed!")
        if e.stdout:
            logger.error(e.stdout)
        return False
        
    except FileNotFoundError:
        logger.warning("⚠️ BIDS validator (deno) not found. Skipping validation.")
        logger.info("To install: https://deno.land/manual/getting_started/installation")
        return True  # Don't fail if validator is not available


def validate_participants_data(df_participants: pd.DataFrame, 
                             df_variables: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate participants data against variable definitions.
    
    Args:
        df_participants: Participants DataFrame
        df_variables: Variables definition DataFrame
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'missing_variables': [],
        'type_mismatches': [],
        'warnings': []
    }
    
    # Check for missing variables
    expected_vars = df_variables[ColumnNames.VARIABLE_NAME].tolist()
    actual_vars = df_participants.columns.tolist()
    
    missing_vars = [var for var in expected_vars if var not in actual_vars]
    results['missing_variables'] = missing_vars
    
    if missing_vars:
        results['warnings'].append(f"Missing variables in participants data: {missing_vars}")
    
    # Validate data types
    dtype_map = dict(zip(df_variables[ColumnNames.VARIABLE_NAME], 
                        df_variables[ColumnNames.DATA_TYPE].str.lower()))
    
    for col in df_participants.columns:
        if col in dtype_map:
            expected_type = dtype_map[col]
            actual_dtype = str(df_participants[col].dtype)
            
            # Simple type checking
            if expected_type == 'integer' and 'int' not in actual_dtype.lower():
                results['type_mismatches'].append((col, expected_type, actual_dtype))
            elif expected_type == 'float' and 'float' not in actual_dtype.lower():
                results['type_mismatches'].append((col, expected_type, actual_dtype))
    
    return results


def check_file_permissions(file_path: str) -> bool:
    """
    Check if a file can be written to.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if writable, False otherwise
    """
    try:
        # Try to create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Test write permission
        with open(file_path, 'a'):
            pass
        return True
        
    except (PermissionError, OSError):
        return False


def validate_output_permissions(output_folder: str) -> None:
    """
    Validate that output folder is writable.
    
    Args:
        output_folder: Path to output folder
        
    Raises:
        ValidationError: If folder is not writable
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        # Test write permission with a temporary file
        test_file = os.path.join(output_folder, '.test_write_permission')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
    except (PermissionError, OSError) as e:
        raise ValidationError(f"Cannot write to output folder {output_folder}: {str(e)}")


def sanitize_for_tsv(value: Any) -> str:
    """
    Sanitize a value for inclusion in TSV files.
    
    Args:
        value: Value to sanitize
        
    Returns:
        Sanitized string value
    """
    if pd.isna(value):
        return 'n/a'
    
    # Convert to string
    str_value = str(value)
    
    # Replace problematic characters
    sanitized = re.sub(r'[\t\n\r]', ' ', str_value)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Handle special cases
    if sanitized.lower() in ['', 'nan', 'none', 'null']:
        return 'n/a'
    
    return sanitized
