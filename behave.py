# main.py
import os
import glob
import sys
import logging
import pandas as pd
import subprocess

def print_header():
    header = """
▗▖  ▗▖▗▄▄▖ ▗▄▄▄▖    ▗▖    ▗▄▖ ▗▄▄▖      ▗▄▄▖▗▄▄▖  ▗▄▖ ▗▄▄▄▄▖
▐▛▚▞▜▌▐▌ ▐▌  █      ▐▌   ▐▌ ▐▌▐▌ ▐▌    ▐▌   ▐▌ ▐▌▐▌ ▐▌   ▗▞▘
▐▌  ▐▌▐▛▀▚▖  █      ▐▌   ▐▛▀▜▌▐▛▀▚▖    ▐▌▝▜▌▐▛▀▚▖▐▛▀▜▌ ▗▞▘  
▐▌  ▐▌▐▌ ▐▌▗▄█▄▖    ▐▙▄▄▖▐▌ ▐▌▐▙▄▞▘    ▝▚▄▞▘▐▌ ▐▌▐▌ ▐▌▐▙▄▄▄▖
             MRI-Lab Graz - Survey to BIDS Converter               
"""
    print(header)

"""
Script Name: main.py
Description: Converts survey data to BIDS format
Author: Karl Koschutnig
Date Created: 3.11.2024
Last Modified: 31.01.2025
Version: 1.1

----------------------------------------------------------
"""
print_header()

sys.path.append(os.path.abspath("code"))

try:
    from import_dataset import convert_excel_to_json_updated
    from read_session_data import create_bids_structure_and_copy_data
    # Import the new function
    from participants import convert_demographics_to_participants
except ImportError as e:
    print(f"Error importing modules: {e}")

logging.basicConfig(level=logging.debug, format='%(asctime)s - %(levelname)s - %(message)s')

anonymize = False  # or False, as needed


def cleanup_unused_task_json(output_folder):
    """
    Delete task-*.json files in the root folder if no corresponding *_task-*.tsv files exist.
    """
    print("🔍 Checking for unused task JSON files...")

    # Find all task-*.json files in the root output folder
    task_json_files = glob.glob(os.path.join(output_folder, "task-*_beh.json"))

    for task_json in task_json_files:
        # Extract the task name from the JSON filename
        task_name = os.path.basename(task_json).replace("task-", "").replace("_beh.json", "")

        # Search for matching TSV files in the BIDS rawdata directory
        matching_tsv_files = glob.glob(os.path.join(output_folder, "**", f"*task-{task_name}_beh.tsv"), recursive=True)

        if not matching_tsv_files:
            print(f"🗑️  No TSV files found for {task_name}. Deleting {task_json}...")
            os.remove(task_json)
        else:
            print(f"✅ Task {task_name} is used. Keeping {task_json}.")

    print("✅ Cleanup completed.")


import subprocess

def validate_bids(bids_rawdata_folder):
    """
    Run the BIDS Validator using Deno and capture all output.
    """
    print("🚀 Running BIDS Validator...")

    # Construct the validation command
    validator_command = [
        "deno", "run", "-ERN", "jsr:@bids/validator",
        bids_rawdata_folder, "--ignoreWarnings", "-v"
    ]

    try:
        # Combine stdout and stderr
        result = subprocess.run(
            validator_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            text=True
        )
        print("✅ BIDS validation completed successfully!")
        print(result.stdout)  # This now includes both stdout and stderr
    except subprocess.CalledProcessError as e:
        print("❌ BIDS validation failed!")
        # When an error occurs, use e.output which contains the combined output.
        print(e.output)


def main():
    # Collect all session files, excluding temporary files and variables file
    session_files = [
        f for f in glob.glob('./data/*.xlsx')
        if not os.path.basename(f).startswith('~$') and os.path.basename(f) != 'participants_dataset.xlsx'
    ]
    if not session_files:
        logging.error("No session files found in './data/'")
        return

    output_folder = './bids/rawdata'  # Adjust as needed

    # Path to the variables definition Excel file
    variables_file = './data/participants_dataset.xlsx'

    # Aggregate participant data from all session files
    participant_data_frames = []
    for session_file in session_files:
        print(f"🏋Working in session file: {session_file}")
        try:
            df_session = pd.read_excel(session_file)
            participant_data_frames.append(df_session)
        except Exception as e:
            logging.warning(f"Could not read session file {session_file}: {e}")

    # Concatenate all participant data and remove duplicates
    df_all_sessions = pd.concat(participant_data_frames, ignore_index=True)
    df_all_sessions.drop_duplicates(subset='id', inplace=True)

    # Call the function to create participants.tsv and participants.json
    demographics_file = "data/demographics.xlsx"
    convert_demographics_to_participants(demographics_file, variables_file, output_folder)
    
    #convert_excel_to_participants(df_all_sessions, variables_file, output_folder)

# Process each questionnaire
    for excel_file in glob.glob('./resources/*.xlsx'):
        if os.path.basename(excel_file) == 'participants_dataset.xlsx':
            continue  # Skip the variables definition file
        
        logging.debug(f"Processing Questionnaire File: {excel_file}")

        try:
            # Load the Excel file to check the number of sheets
            xls = pd.ExcelFile(excel_file)
            if len(xls.sheet_names) == 1:
                logging.error(f"Skipping {excel_file}: Expected 2 sheets, found {len(xls.sheet_names)}")
                continue  # Skip this file and move to the next one
        except Exception as e:
            logging.error(f"Error reading {excel_file}: {e}")
            continue  # Skip this file and move to the next one
        
        # Extract the task name from the file name
        task_name = os.path.splitext(os.path.basename(excel_file))[0].upper()
        logging.debug(f"Task name: {task_name}")

        # Generate the output JSON file path
        output_json_file = os.path.join(output_folder, f'task-{task_name.lower()}_beh.json')

        # Convert Excel to JSON (ensuring the function is defined)
        convert_excel_to_json_updated(excel_file, output_json_file, anonymize)

        # Process each session file for the current task
        for session_file in session_files:
            logging.debug(f"Session File: {session_file}")

            # Call the function to process session data and create BIDS structure
            create_bids_structure_and_copy_data(session_file, task_name, excel_file, output_folder)
            

if __name__ == "__main__":
    main()
    output_folder = './bids/rawdata' 
# 🔹 Perform cleanup of unused task JSON files
    cleanup_unused_task_json(output_folder)

# 🔹 Run BIDS validation
    validate_bids(output_folder)

