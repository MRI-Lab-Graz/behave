"""
Configuration module for BEHAVE - BIDS behavioral data converter.

This module contains configuration settings, constants, and utility classes
used throughout the BEHAVE application.
"""

from dataclasses import dataclass
from typing import List, Optional
import logging


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
    
    # Session file columns
    SUBJECT_ID = 'id'
    SESSION = 'ses'
    
    # Variable definition columns
    VARIABLE_NAME = 'VariableName'
    DATA_TYPE = 'DataType'
    DESCRIPTION = 'Description'
    LEVELS = 'Levels'
    
    # Metadata sheet columns
    KEY_NAME = 'key name'
    DESCRIPTION_META = 'description'


class DataTypes:
    """Data type constants for BIDS conversion."""
    
    INTEGER = 'integer'
    FLOAT = 'float'
    CAT_NUM = 'cat_num'
    CAT_STRING = 'cat_string'
    STRING = 'string'


class BIDSPaths:
    """BIDS directory and file naming conventions."""
    
    RAWDATA = 'rawdata'
    PARTICIPANTS_TSV = 'participants.tsv'
    PARTICIPANTS_JSON = 'participants.json'
    DATASET_DESCRIPTION_JSON = 'dataset_description.json'
    
    @staticmethod
    def get_task_json_filename(task_name: str) -> str:
        """Generate BIDS-compliant task JSON filename."""
        return f'task-{task_name.lower()}_beh.json'
    
    @staticmethod
    def get_task_tsv_filename(subject_id: str, session: str, task_name: str) -> str:
        """Generate BIDS-compliant task TSV filename."""
        return f'{subject_id}_ses-{session}_task-{task_name.lower()}_beh.tsv'
    
    @staticmethod
    def get_subject_session_path(subject_id: str, session: str) -> str:
        """Generate BIDS-compliant subject/session path."""
        return f'{subject_id}/ses-{session}/beh'


def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration for the entire application.
    
    Args:
        debug: Enable debug level logging
        log_file: Optional log file path
    """
    config = BehaveConfig()
    level = logging.DEBUG if debug else logging.INFO
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format=config.log_format,
        handlers=handlers,
        force=True  # Override any existing logging configuration
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('pandas').setLevel(logging.WARNING)
    logging.getLogger('openpyxl').setLevel(logging.WARNING)


# Create default configuration instance
DEFAULT_CONFIG = BehaveConfig()
