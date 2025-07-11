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
from pathlib import Path
from typing import List

# Import BEHAVE modules
from config import BehaveConfig, setup_logging
from excel_handler import find_session_files
from validators import validate_folder_structure, validate_bids_structure, validate_output_permissions
from bids_converter import BIDSConverter, cleanup_unused_json_files


def print_header():
    """Print the BEHAVE header with ASCII art and welcome message."""
    header = """
▗▖  ▗▖▗▄▄▖ ▗▄▄▄▖    ▗▖    ▗▄▖ ▗▄▄▖      ▗▄▄▖▗▄▄▖  ▗▄▖ ▗▄▄▄▄▖
▐▛▚▞▜▌▐▌ ▐▌  █      ▐▌   ▐▌ ▐▌▐▌ ▐▌    ▐▌   ▐▌ ▐▌▐▌ ▐▌   ▗▞▘
▐▌  ▐▌▐▛▀▚▖  █      ▐▌   ▐▛▀▜▌▐▛▀▚▖    ▐▌▝▜▌▐▛▀▚▖▐▛▀▜▌ ▗▞▘  
▐▌  ▐▌▐▌ ▐▌▗▄█▄▖    ▐▙▄▄▖▐▌ ▐▌▐▙▄▞▘    ▝▚▄▞▘▐▌ ▐▌▐▌ ▐▌▐▙▄▄▄▖
             MRI-Lab Graz - Survey to BIDS Converter              
        """
    print(header)
    print("🎓 Welcome to BEHAVE! Converting your Excel survey data to BIDS format...")
    print("📚 For help and examples, visit: https://github.com/your-repo/behave")
    print("💡 Use --debug flag for detailed information during conversion\n")


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


def check_prerequisites() -> bool:
    """
    Check if all required files and folders exist before starting conversion.
    Provides helpful feedback for students about missing requirements.
    """
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Check and install missing packages if needed
    return check_and_install_missing_packages()


def validate_excel_structure_preview(file_path: str, file_type: str) -> bool:
    """
    Validate Excel file structure and provide detailed feedback.
    """
    try:
        import pandas as pd
        
        # Load Excel file
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names
        
        print(f"📋 Analyzing {file_type}: {os.path.basename(file_path)}")
        print(f"   Found {len(sheets)} sheets: {', '.join(sheets)}")
        
        if file_type == "task definition":
            if len(sheets) < 3:
                print(f"   ❌ Task files need at least 3 sheets (found {len(sheets)})")
                print("   Required sheets: 1) Items, 2) Task Description, 3) Non-Likert")
                return False
            else:
                print("   ✅ Sufficient number of sheets")
        
        elif file_type == "demographics":
            df = pd.read_excel(file_path, sheet_name=0)
            print(f"   📊 {len(df)} participants, {len(df.columns)} columns")
            
            if 'id' not in df.columns.str.lower():
                print("   ❌ Missing 'id' column for participant IDs")
                return False
            else:
                print("   ✅ Participant ID column found")
        
        elif file_type == "variables":
            if len(sheets) < 2:
                print("   ❌ Variables file needs 2 sheets: Variables + Dataset Description")
                return False
            else:
                print("   ✅ Variables and dataset description sheets found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading {file_type}: {str(e)}")
        return False


def print_file_structure_help():
    """Print helpful information about expected file structure."""
    print("\n📁 Expected File Structure:")
    print("   your-project/")
    print("   ├── data/")
    print("   │   └── YourStudy/")
    print("   │       ├── demographics.xlsx          # Participant info")
    print("   │       ├── participants_dataset.xlsx  # Variable definitions")
    print("   │       └── session1.xlsx              # Response data")
    print("   ├── resources/")
    print("   │   ├── questionnaire1.xlsx           # Task definitions")
    print("   │   └── questionnaire2.xlsx")
    print("   └── output/                            # BIDS output will go here")
    print()


def print_success_summary(paths: dict, task_count: int, participant_count: int):
    """Print a comprehensive success summary for students."""
    print("\n" + "="*70)
    print("🎉 CONVERSION COMPLETED SUCCESSFULLY! 🎉")
    print("="*70)
    print()
    print("📊 Summary:")
    print(f"   • Converted {task_count} questionnaire(s)")
    print(f"   • Processed {participant_count} participant(s)")
    print(f"   • Output location: {paths['output_folder']}")
    print()
    print("📋 Generated BIDS files:")
    print("   ✅ participants.tsv         - Demographic data")
    print("   ✅ participants.json        - Variable descriptions")
    print("   ✅ dataset_description.json - Study metadata")
    print("   ✅ task-*_beh.json         - Questionnaire definitions")
    print("   ✅ sub-*/*_beh.tsv         - Individual responses")
    print()
    print("🔍 Next steps:")
    print("   1. Review the output folder structure")
    print("   2. Check participants.tsv for correct demographic data")
    print("   3. Verify task JSON files contain your questionnaire items")
    print("   4. Upload to your BIDS repository or analysis pipeline")
    print()
    print("📚 Need help? Check the documentation:")
    print("   • GitHub: https://github.com/your-repo/behave")
    print("   • BIDS Specification: https://bids.neuroimaging.io/")
    print("="*70)


def check_and_activate_virtual_environment():
    """
    Check if we're in a virtual environment and automatically activate one if needed.
    This makes the script more user-friendly for students who don't understand virtual environments.
    """
    import subprocess
    import sys
    from pathlib import Path
    
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is already active")
        return True
    
    # Look for common virtual environment locations
    script_dir = Path(__file__).parent
    venv_paths = [
        script_dir / '.behave',  # uv setup
        script_dir / 'venv',     # standard venv
        script_dir / '.venv',    # common alternative
        script_dir / 'env',      # another common name
    ]
    
    for venv_path in venv_paths:
        if venv_path.exists():
            print(f"🔍 Found virtual environment at: {venv_path}")
            
            # Determine activation script path
            if sys.platform == "win32":
                activate_script = venv_path / 'Scripts' / 'python.exe'
            else:
                activate_script = venv_path / 'bin' / 'python'
            
            if activate_script.exists():
                print("🚀 Automatically switching to virtual environment...")
                
                # Re-execute the script with the virtual environment Python
                try:
                    # Get all command line arguments
                    args = sys.argv[1:]  # Skip the script name
                    
                    # Execute the script with the virtual environment Python
                    result = subprocess.run([str(activate_script), __file__] + args, 
                                          check=False)
                    sys.exit(result.returncode)
                    
                except Exception as e:
                    print(f"❌ Failed to switch to virtual environment: {e}")
                    break
    
    # If we get here, no virtual environment was found or activated
    print("⚠️  No virtual environment found or activated")
    print("🎯 For best results, please set up a virtual environment:")
    print("   1. Run: ./uv_setup.sh (recommended)")
    print("   2. Or: python -m venv .venv && source .venv/bin/activate")
    print("   3. Then install dependencies: pip install -r requirements.txt")
    print()
    print("💡 Continuing without virtual environment...")
    return False


def check_and_install_missing_packages():
    """
    Check for missing packages and offer to install them automatically.
    This helps students who might not have all dependencies installed.
    """
    missing_packages = []
    
    # Check for required packages
    try:
        import pandas
        print(f"✅ pandas version: {pandas.__version__}")
    except ImportError:
        missing_packages.append("pandas")
    
    try:
        import openpyxl
        print("✅ openpyxl available")
        # Test if openpyxl is working by attempting to access its module
        _ = openpyxl.__version__
    except ImportError:
        missing_packages.append("openpyxl")
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print()
        
        # Ask user if they want to install missing packages
        try:
            response = input("🤖 Would you like me to install the missing packages? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                print("📦 Installing missing packages...")
                
                import subprocess
                for package in missing_packages:
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                     check=True, capture_output=True)
                        print(f"✅ Successfully installed {package}")
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Failed to install {package}: {e}")
                        return False
                
                print("🎉 All packages installed successfully!")
                return True
            else:
                print("📋 Please install the missing packages manually:")
                for package in missing_packages:
                    print(f"   pip install {package}")
                return False
                
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Installation cancelled")
            return False
    
    return True


def main():
    """Main function orchestrating the entire conversion process."""
    # Check and activate virtual environment automatically
    check_and_activate_virtual_environment()
    
    # Parse arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(debug=args.debug, log_file=args.log_file)
    logger = logging.getLogger(__name__)
    
    print_header()
    logger.info("Starting BEHAVE conversion process")
    
    try:
        # Check prerequisites
        if not check_prerequisites():
            logger.error("Prerequisite check failed")
            print("\n❌ Setup incomplete. Please resolve the issues above and try again.")
            sys.exit(1)
        
        # Check and activate virtual environment
        check_and_activate_virtual_environment()
        
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
        print_success_summary(paths, len(task_names), len(session_files))
        
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
