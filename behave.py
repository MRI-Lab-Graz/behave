#!/usr/bin/env python3
"""
BEHAVE - Behavioral Data to BIDS Converter

A modular command-line tool that converts behavioral data from Excel files 
into BIDS-compliant JSON and TSV files for neuroimaging data repositories.

Author: MRI-Lab Graz
License: MIT
"""

import os
import sys
import argparse
import logging
import glob
from pathlib import Path
from typing import List

# Import BEHAVE modules
from config import BehaveConfig, setup_logging, DEFAULT_CONFIG
from excel_handler import find_session_files, validate_file_exists
from validators import validate_folder_structure, validate_bids_structure, validate_output_permissions
from bids_converter import BIDSConverter, cleanup_unused_json_files


def print_header():
    """Print the BEHAVE header with ASCII art."""
    header = """
▗▖  ▗▖▗▄▄▖ ▗▄▄▄▖    ▗▖    ▗▄▖ ▗▄▄▖      ▗▄▄▖▗▄▄▖  ▗▄▖ ▗▄▄▄▄▖
▐▛▚▞▜▌▐▌ ▐▌  █      ▐▌   ▐▌ ▐▌▐▌ ▐▌    ▐▌   ▐▌ ▐▌▐▌ ▐▌   ▗▞▘
▐▌  ▐▌▐▛▀▚▖  █      ▐▌   ▐▛▀▜▌▐▛▀▚▖    ▐▌▝▜▌▐▛▀▚▖▐▛▀▜▌ ▗▞▘  
▐▌  ▐▌▐▌ ▐▌▗▄█▄▖    ▐▙▄▄▖▐▌ ▐▌▐▙▄▞▘    ▝▚▄▞▘▐▌ ▐▌▐▌ ▐▌▐▙▄▄▄▖
             MRI-Lab Graz - Survey to BIDS Converter              
        """
    print(header)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="""Process data and resources folders to convert Excel files into BIDS-compliant JSON and TSV formats.
        
        This script expects:
        - A data folder containing session Excel files, demographics.xlsx, and participants_dataset.xlsx
        - A resources folder containing task definition Excel files
        
        Each task definition file should have 3 sheets:
        1. Main sheet with item definitions (itemname, itemdescription, likert_scale, etc.)
        2. Task description metadata (key name, description)
        3. Non-Likert variable definitions (key name, description)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-d', '--data',
        required=True,
        help="Path to the data folder containing session files and demographics"
    )
    
    parser.add_argument(
        '-r', '--resources',
        required=True,
        help="Path to the resources folder containing task definition Excel files"
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help="Path to the BIDS output folder"
    )
    
    parser.add_argument(
        "-s", "--study",
        required=True,
        help="Study name/ID (e.g., PK01, MyStudy)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--anonymize",
        action="store_true",
        help="Anonymize item descriptions in output files"
    )
    
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip BIDS validation (faster but less thorough)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Path to log file (optional)"
    )
    
    return parser.parse_args()


def setup_paths(args: argparse.Namespace) -> dict:
    """Set up and validate all required paths."""
    paths = {
        'data_folder': os.path.join(args.data, args.study),
        'resources_folder': args.resources,
        'output_folder': os.path.join(args.output, args.study, 'rawdata'),
        'demographics_file': os.path.join(args.data, args.study, 'demographics.xlsx'),
        'variables_file': os.path.join(args.data, args.study, 'participants_dataset.xlsx')
    }
    
    # Log all paths
    logger = logging.getLogger(__name__)
    for name, path in paths.items():
        logger.info(f"{name}: {path}")
    
    return paths


def find_task_files(resources_folder: str) -> List[str]:
    """Find all task definition Excel files in resources folder."""
    task_files = []
    
    for file_path in Path(resources_folder).glob("*.xlsx"):
        # Skip temporary files
        if file_path.name.startswith('~$'):
            continue
        
        task_files.append(str(file_path))
    
    logger = logging.getLogger(__name__)
    logger.info(f"Found {len(task_files)} task definition files")
    
    return task_files


def process_task_definitions(task_files: List[str], output_folder: str, 
                           anonymize: bool, converter: BIDSConverter) -> List[str]:
    """Process all task definition files and return list of task names."""
    logger = logging.getLogger(__name__)
    task_names = []
    
    for task_file in task_files:
        try:
            # Extract task name from filename
            task_name = Path(task_file).stem.upper()
            task_names.append(task_name)
            
            logger.debug(f"Processing task definition: {task_file} -> {task_name}")
            
            # Generate output JSON filename
            output_json = os.path.join(output_folder, f'task-{task_name.lower()}_beh.json')
            
            # Convert Excel to JSON
            converter.convert_excel_to_json(task_file, output_json, anonymize)
            
        except Exception as e:
            logger.error(f"Failed to process task file {task_file}: {str(e)}")
            continue
    
    return task_names


def process_session_data(session_files: List[str], task_files: List[str], 
                        task_names: List[str], output_folder: str, 
                        converter: BIDSConverter) -> None:
    """Process all session files for all tasks."""
    logger = logging.getLogger(__name__)
    
    for session_file in session_files:
        logger.debug(f"Processing session file: {session_file}")
        
        for task_file, task_name in zip(task_files, task_names):
            try:
                converter.create_bids_structure(
                    session_file, task_name, task_file, output_folder
                )
            except Exception as e:
                logger.warning(f"Failed to process {session_file} for task {task_name}: {str(e)}")
                continue


def main():
    """Main function orchestrating the entire conversion process."""
    # Parse arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(debug=args.debug, log_file=args.log_file)
    logger = logging.getLogger(__name__)
    
    print_header()
    logger.info("Starting BEHAVE conversion process")
    
    try:
        # Set up paths
        paths = setup_paths(args)
        
        # Validate folder structure and permissions
        validate_folder_structure(paths['data_folder'], paths['resources_folder'])
        validate_output_permissions(paths['output_folder'])
        
        # Create output directory
        os.makedirs(paths['output_folder'], exist_ok=True)
        
        # Initialize converter with configuration
        config = BehaveConfig(anonymize_questions=args.anonymize)
        converter = BIDSConverter(config)
        
        # Convert demographics to participants files
        logger.info("Converting demographics to participants files...")
        converter.convert_demographics_to_participants(
            paths['demographics_file'],
            paths['variables_file'],
            paths['output_folder']
        )
        
        # Find session files
        logger.info("Finding session files...")
        session_files = find_session_files(paths['data_folder'])
        
        if not session_files:
            logger.error(f"No session files found in {paths['data_folder']}")
            sys.exit(1)
        
        # Find and process task definition files
        logger.info("Processing task definitions...")
        task_files = find_task_files(paths['resources_folder'])
        
        if not task_files:
            logger.error(f"No task definition files found in {paths['resources_folder']}")
            sys.exit(1)
        
        # Process task definitions (Excel -> JSON)
        task_names = process_task_definitions(
            task_files, paths['output_folder'], args.anonymize, converter
        )
        
        # Process session data (Excel -> TSV)
        logger.info("Processing session data...")
        process_session_data(
            session_files, task_files, task_names, paths['output_folder'], converter
        )
        
        # Cleanup unused JSON files
        logger.info("Cleaning up unused files...")
        cleanup_unused_json_files(paths['output_folder'])
        
        # Validate BIDS structure
        if not args.skip_validation:
            logger.info("Validating BIDS structure...")
            validation_success = validate_bids_structure(paths['output_folder'])
            
            if validation_success:
                logger.info("✅ BIDS validation passed!")
            else:
                logger.warning("⚠️ BIDS validation failed or skipped")
        else:
            logger.info("Skipping BIDS validation")
        
        logger.info("🎉 BEHAVE conversion completed successfully!")
        print(f"\n✅ Output written to: {paths['output_folder']}")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        if args.debug:
            logger.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    main()
