"""
Excel file handling and validation module for BEHAVE.

This module provides functions for safely loading, validating, and processing
Excel files used in the BEHAVE behavioral data conversion pipeline.
"""

import os
import logging
import pandas as pd
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from config import BehaveConfig, ColumnNames, DataTypes, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ExcelValidationError(Exception):
    """Raised when Excel file validation fails."""
    pass


def load_excel_safely(file_path: str, sheet_name: Any = 0) -> pd.DataFrame:
    """
    Safely load an Excel file with comprehensive error handling.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Sheet name or index to load
        
    Returns:
        DataFrame containing the Excel data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ExcelValidationError: If the file cannot be read
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        logger.debug(f"Successfully loaded Excel file: {file_path}, sheet: {sheet_name}")
        return df
    except Exception as e:
        error_msg = f"Error reading Excel file {file_path}, sheet {sheet_name}: {str(e)}"
        logger.error(error_msg)
        raise ExcelValidationError(error_msg) from e


def validate_excel_structure(df: pd.DataFrame, required_columns: List[str], 
                           file_context: str = "") -> None:
    """
    Validate that a DataFrame contains required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        file_context: Context string for error messages
        
    Raises:
        ExcelValidationError: If required columns are missing
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns in {file_context}: {missing_cols}"
        logger.error(error_msg)
        raise ExcelValidationError(error_msg)


def normalize_column_names(df: pd.DataFrame, lowercase: bool = True) -> pd.DataFrame:
    """
    Normalize DataFrame column names by stripping whitespace and optionally converting to lowercase.
    
    Args:
        df: DataFrame to normalize
        lowercase: Whether to convert to lowercase
        
    Returns:
        DataFrame with normalized column names
    """
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.str.strip()
    if lowercase:
        df_copy.columns = df_copy.columns.str.lower()
    return df_copy


def load_and_validate_excel(excel_file: str, config: BehaveConfig = DEFAULT_CONFIG) -> Dict[str, pd.DataFrame]:
    """
    Load and validate the Excel file structure for task definitions.
    
    Args:
        excel_file: Path to the Excel file
        config: Configuration object
        
    Returns:
        Dictionary with DataFrames for main, task_desc, and nonlikert sheets
        
    Raises:
        ExcelValidationError: If file structure is invalid
    """
    logger.info(f"Loading and validating Excel file: {excel_file}")
    
    try:
        xls = pd.ExcelFile(excel_file)
    except Exception as e:
        raise ExcelValidationError(f"Cannot read Excel file {excel_file}: {str(e)}") from e
    
    # Check for the expected number of sheets
    if len(xls.sheet_names) < config.min_required_sheets:
        raise ExcelValidationError(
            f"Excel file {excel_file} must contain at least {config.min_required_sheets} sheets. "
            f"Found: {len(xls.sheet_names)}"
        )
    
    # Load the sheets into DataFrames
    try:
        df_main = load_excel_safely(excel_file, sheet_name=0)
        df_task_desc = load_excel_safely(excel_file, sheet_name=1)
        df_nonlikert = load_excel_safely(excel_file, sheet_name=2)
    except Exception as e:
        raise ExcelValidationError(f"Error loading sheets from {excel_file}: {str(e)}") from e
    
    # Normalize column names
    df_main = normalize_column_names(df_main, lowercase=False)  # Keep case for main sheet
    df_task_desc = normalize_column_names(df_task_desc, lowercase=True)
    df_nonlikert = normalize_column_names(df_nonlikert, lowercase=True)
    
    # Validate required columns
    required_main_cols = [ColumnNames.ITEM_NAME, ColumnNames.ITEM_DESCRIPTION]
    validate_excel_structure(df_main, required_main_cols, f"{excel_file} (main sheet)")
    
    required_meta_cols = [ColumnNames.KEY_NAME, ColumnNames.DESCRIPTION_META]
    validate_excel_structure(df_task_desc, required_meta_cols, f"{excel_file} (task description sheet)")
    validate_excel_structure(df_nonlikert, required_meta_cols, f"{excel_file} (non-likert sheet)")
    
    logger.info(f"Successfully validated Excel file: {excel_file}")
    
    return {
        'main': df_main,
        'task_desc': df_task_desc,
        'nonlikert': df_nonlikert
    }


def load_session_file(session_file: str) -> pd.DataFrame:
    """
    Load and validate a session file.
    
    Args:
        session_file: Path to the session Excel file
        
    Returns:
        DataFrame with normalized session data
        
    Raises:
        ExcelValidationError: If file is invalid
    """
    logger.debug(f"Loading session file: {session_file}")
    
    df_session = load_excel_safely(session_file)
    
    # Validate required columns
    required_cols = DEFAULT_CONFIG.required_session_columns
    
    # Check if columns exist (case-insensitive)
    available_cols = [col.lower() for col in df_session.columns]
    missing_cols = []
    
    for req_col in required_cols:
        if req_col.lower() not in available_cols:
            missing_cols.append(req_col)
    
    if missing_cols:
        raise ExcelValidationError(
            f"Session file {session_file} must contain columns: {missing_cols}"
        )
    
    return df_session


def load_demographics_file(demographics_file: str) -> pd.DataFrame:
    """
    Load and validate demographics file.
    
    Args:
        demographics_file: Path to demographics Excel file
        
    Returns:
        DataFrame with normalized demographics data
    """
    logger.info(f"Loading demographics file: {demographics_file}")
    
    df_demo = load_excel_safely(demographics_file)
    df_demo = normalize_column_names(df_demo, lowercase=True)
    
    return df_demo


def load_variables_file(variables_file: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load variables definition file with dataset description.
    
    Args:
        variables_file: Path to participants_dataset.xlsx
        
    Returns:
        Tuple of (variables DataFrame, dataset description dict)
    """
    logger.info(f"Loading variables file: {variables_file}")
    
    # Load variables definition (first sheet)
    df_variables = load_excel_safely(variables_file, sheet_name=0)
    
    # Validate required columns
    required_cols = [ColumnNames.VARIABLE_NAME, ColumnNames.DATA_TYPE, ColumnNames.DESCRIPTION]
    validate_excel_structure(df_variables, required_cols, f"{variables_file} (variables sheet)")
    
    # Normalize variable names
    df_variables[ColumnNames.VARIABLE_NAME] = df_variables[ColumnNames.VARIABLE_NAME].str.strip().str.lower()
    
    # Load dataset description (second sheet)
    try:
        df_description = load_excel_safely(variables_file, sheet_name=1)
        
        if df_description.shape[1] < 2:
            raise ExcelValidationError(
                f"Dataset description sheet in {variables_file} must contain at least two columns (key, value)."
            )
        
        # Convert to dictionary
        dataset_description = dict(
            zip(df_description.iloc[:, 0].astype(str), df_description.iloc[:, 1].astype(str))
        )
        
    except Exception as e:
        logger.warning(f"Could not load dataset description from {variables_file}: {str(e)}")
        dataset_description = {}
    
    return df_variables, dataset_description


def normalize_item_name(item_name: str) -> str:
    """
    Normalize item names by converting the prefix to uppercase only if they end with a number.
    
    Args:
        item_name: The item name to normalize
        
    Returns:
        Normalized item name
    """
    item_name = str(item_name)  # Ensure it's a string
    match = re.match(r'([A-Za-z]+)[\s\-_]?(\d+)$', item_name)  # Match only items ending in a number
    if match:
        return f"{match.group(1).upper()}{match.group(2)}"  # Convert prefix to uppercase
    return item_name  # Return unchanged if it doesn't match


def clean_text_data(value: Any) -> Any:
    """
    Clean text data by removing problematic characters for TSV files.
    
    Args:
        value: Value to clean
        
    Returns:
        Cleaned value
    """
    if isinstance(value, str):
        # Replace new lines, carriage returns, and commas with space
        cleaned = re.sub(r'[\n\r,\t]', ' ', value)
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    return value


def find_session_files(data_folder: str, exclude_files: Optional[List[str]] = None) -> List[str]:
    """
    Find all session Excel files in the data folder.
    
    Args:
        data_folder: Path to data folder
        exclude_files: List of filenames to exclude
        
    Returns:
        List of session file paths
    """
    if exclude_files is None:
        exclude_files = ['participants_dataset.xlsx', 'demographics.xlsx']
    
    session_files = []
    
    for file_path in Path(data_folder).glob("*.xlsx"):
        filename = file_path.name
        
        # Skip temporary files and excluded files
        if filename.startswith('~$') or filename in exclude_files:
            continue
            
        session_files.append(str(file_path))
    
    logger.info(f"Found {len(session_files)} session files in {data_folder}")
    
    return session_files


def validate_file_exists(file_path: str, file_type: str = "file") -> None:
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to check
        file_type: Type description for error messages
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required {file_type} not found: {file_path}")


def convert_data_types(df: pd.DataFrame, dtype_map: Dict[str, str], 
                      config: BehaveConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """
    Convert DataFrame columns to appropriate data types based on mapping.
    
    Args:
        df: DataFrame to convert
        dtype_map: Mapping of column names to data types
        config: Configuration object
        
    Returns:
        DataFrame with converted data types
    """
    df_converted = df.copy()
    
    for col in df_converted.columns:
        if col not in dtype_map:
            continue
            
        data_type = dtype_map[col].lower()
        
        try:
            if data_type == DataTypes.INTEGER:
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce').astype(pd.Int64Dtype())
            elif data_type == DataTypes.FLOAT:
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
            elif data_type == DataTypes.CAT_NUM:
                numeric_col = pd.to_numeric(df_converted[col], errors='coerce')
                if numeric_col.notna().all() and (numeric_col % 1 == 0).all():
                    df_converted[col] = numeric_col.astype(pd.Int64Dtype())
                else:
                    df_converted[col] = df_converted[col].astype(str)
            elif data_type == DataTypes.CAT_STRING:
                df_converted[col] = df_converted[col].astype(str)
            elif data_type == DataTypes.STRING:
                df_converted[col] = df_converted[col].astype(str)
                
        except Exception as e:
            logger.warning(f"Could not convert column {col} to {data_type}: {str(e)}")
    
    return df_converted
