import os
import sys
import argparse
import logging
import glob
import json
import math
import re
import pandas as pd
import subprocess
from colorama import Fore, Style, init

anonymize = False  # or False, as needed


# # Set up argument parsing
# parser = argparse.ArgumentParser(
#         description="""Process data and resources folders to convert Excel files into JSON and TSV formats.
#         This script expects specific Excel files in the resources folder:
#         - 'demographics.xlsx' for demographic data
#         - 'participants_variables.xlsx' for variable definitions and dataset descriptions.
#         """
#     )
# parser.add_argument("-s", "--study", required=True, help="Study ID (e.g., PK01)")
# parser.add_argument("--debug", action="store_true", help="Enable debug logging")
# args = parser.parse_args()


def print_header():
    header = """
▗▖  ▗▖▗▄▄▖ ▗▄▄▄▖    ▗▖    ▗▄▖ ▗▄▄▖      ▗▄▄▖▗▄▄▖  ▗▄▖ ▗▄▄▄▄▖
▐▛▚▞▜▌▐▌ ▐▌  █      ▐▌   ▐▌ ▐▌▐▌ ▐▌    ▐▌   ▐▌ ▐▌▐▌ ▐▌   ▗▞▘
▐▌  ▐▌▐▛▀▚▖  █      ▐▌   ▐▛▀▜▌▐▛▀▚▖    ▐▌▝▜▌▐▛▀▚▖▐▛▀▜▌ ▗▞▘  
▐▌  ▐▌▐▌ ▐▌▗▄█▄▖    ▐▙▄▄▖▐▌ ▐▌▐▙▄▞▘    ▝▚▄▞▘▐▌ ▐▌▐▌ ▐▌▐▙▄▄▄▖
             MRI-Lab Graz - Survey to BIDS Converter              
        """
    
print_header()

sys.path.append(os.path.abspath("code"))

def check_mandatory_folders():
    """
    Check if the mandatory /data and /resources folders are mounted.
    """
    if not os.path.exists("/data"):
        raise FileNotFoundError("The /data folder is not mounted. Please mount it using the -v option.")
    if not os.path.exists("/resources"):
        raise FileNotFoundError("The /resources folder is not mounted. Please mount it using the -v option.")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="""Process data and resources folders to convert Excel files into JSON and TSV formats.
        This script expects specific Excel files in the resources folder:
        - 'demographics.xlsx' for demographic data
        - 'participants_variables.xlsx' for variable definitions and dataset descriptions.
        """
    )
    parser.add_argument(
        '-d', '--data',
        required=True,
        help="Path to the data folder where input files will are saved."
    )
    parser.add_argument(
        '-r', '--resources',
        required=True,
        help="Path to the resources folder containing input Excel files."
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help="Path to the BIDS-output folder."
    )
    parser.add_argument(
        "-s", "--study",
        required=True,
        help="Study name (e.g., PK01)")
    
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging")
    
    args = parser.parse_args()
        # Check for mandatory folders
    # check_mandatory_folders()

    # Define the study folder
    study_folder = args.study
    logging.info(f"Study folder: {study_folder}")
    data_folder = args.data
    logging.info(f"Data folder: {data_folder}")
    resources_folder = args.resources
    logging.info(f"Resources folder: {resources_folder}")
    output_folder = args.output
    logging.info(f"Resources folder: {output_folder}")
    
    # List of folders to check
    
    
        # Define paths to expected Excel files
    
    # Set up logging based on the `--debug` flag
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    data_folder = os.path.join(data_folder , study_folder)
    
    folders_to_check = [data_folder, resources_folder]
    
    # Loop over folders and check if they exist
    for folder in folders_to_check:
        if not os.path.exists(folder):
            logging.error(f"Folder '{folder}' does not exist.")
            sys.exit(1)

    # Collect all session files, excluding temporary files and variables file
    session_files = [
        f for f in glob.glob(os.path.join(data_folder, "*.xlsx"))
        if not os.path.basename(f).startswith('~$') and os.path.basename(f) != 'participants_dataset.xlsx'
    ]
    logging.info(f"Found session files: {session_files}")

    if not session_files:
        logging.error(f"No session files found in '{data_folder}'")
        sys.exit(1)

    output_folder = os.path.join(output_folder , study_folder, 'rawdata')
    logging.info(f"Output folder: {output_folder}")

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Path to the variables definition Excel file
    variables_file = os.path.join(data_folder, 'participants_dataset.xlsx')
    logging.info(f"Variables file: {variables_file}")

    # Call the function to create participants.tsv and participants.json
    demographics_file = os.path.join(data_folder, 'demographics.xlsx')
    logging.info(f"Demographics file: {demographics_file}")
    convert_demographics_to_participants(demographics_file, variables_file, output_folder, study_folder)

    # Process each questionnaire
    for excel_file in glob.glob(os.path.join(resources_folder, '*.xlsx')):
        if os.path.basename(excel_file) == 'participants_dataset.xlsx':
            continue  # Skip the variables definition file
        
        logging.debug(f"Processing Questionnaire File: {excel_file}")

        # Extract the task name from the file name
        task_name = os.path.splitext(os.path.basename(excel_file))[0].upper()
        logging.debug(f"Task name: {task_name}")

        # Generate the output JSON file path
        output_json_file = os.path.join(output_folder , f'task-{task_name.lower()}_beh.json')

        # Convert Excel to JSON (ensuring the function is defined)
        convert_excel_to_json_updated(excel_file, output_json_file, anonymize=False)

        # Process each session file for the current task
        for session_file in session_files:
            logging.debug(f"Session File: {session_file}")
            create_bids_structure_and_copy_data(session_file, task_name, excel_file, output_folder, study_folder)

    # Cleanup unused JSON files
    cleanup_unused_task_json(output_folder)

    # Validate BIDS structure
    validate_bids(output_folder)

def cleanup_unused_task_json(output_folder):
    """
    Delete task-*.json files in the root folder if no corresponding *_task-*.tsv files exist.
    """
    logging.info("🔍 Checking for unused task JSON files...")

    # Find all task-*.json files in the root output folder
    task_json_files = glob.glob(os.path.join(output_folder, "task-*_beh.json"))

    for task_json in task_json_files:
        # Extract the task name from the JSON filename
        task_name = os.path.basename(task_json).replace("task-", "").replace("_beh.json", "")

        # Search for matching TSV files in the BIDS rawdata directory
        matching_tsv_files = glob.glob(os.path.join(output_folder, "**", f"*task-{task_name}_beh.tsv"), recursive=True)

        if not matching_tsv_files:
            logging.info(f"🗑️  No TSV files found for {task_name}. Deleting {task_json}...")
            os.remove(task_json)
        else:
            logging.info(f"✅ Task {task_name} is used. Keeping {task_json}.")

    logging.info("✅ Cleanup completed.")

def validate_bids(output_folder):
    """
    Run the BIDS Validator using Deno and capture all output.

    Parameters:
    output_folder (str): Path to the output folder (e.g., './bids/rawdata').
    study_folder (str): Name of the study folder (e.g., 'PK01').
    """
    # Construct the full path to the BIDS directory
    bids_rawdata_folder = os.path.join(output_folder)
    logging.debug(f"Validating BIDS directory: {bids_rawdata_folder}")

    # Check if the BIDS directory exists
    if not os.path.exists(bids_rawdata_folder):
        logging.error(f"BIDS directory does not exist: {bids_rawdata_folder}")
        return

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

def sanitize_text(text):
    """
    Sanitize the text by removing or replacing special characters that could cause issues in TSV/CSV files.
    """
    if pd.isna(text):  # Handle NaN values
        return ""
    # Replace problematic characters with a space or remove them
    sanitized_text = re.sub(r'[,\t\n\r]', ' ', str(text))  # Replace commas, tabs, newlines with spaces
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()  # Remove extra spaces
    return sanitized_text


def convert_excel_to_json_updated(excel_file, output_json_file, anonymize=False):
    # Load both sheets from the Excel file
    # Load the Excel file to check the number of sheets
    xls = pd.ExcelFile(excel_file)
    
    # Check if there is only one sheet
    if len(xls.sheet_names) < 3: 
        #print(excel_file)
        raise ValueError("The Excel file must contain at least three sheets.")
    
    # Load both sheets from the Excel file
    df_main = pd.read_excel(excel_file, sheet_name=0, skiprows=0)

    # Ensure the base directory for the output JSON file exists
    output_dir = os.path.dirname(output_json_file)
    #print(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    df_taskdescription = pd.read_excel(excel_file, sheet_name=1)
    df_nonlikert = pd.read_excel(excel_file, sheet_name=2)

    # Clean up column names (strip whitespace and convert to lowercase) for the main data
    # original: df_main.columns = df_main.columns.str.strip().str.lower()
    df_main.columns = df_main.columns.str.strip()
    df_taskdescription.columns = df_taskdescription.columns.str.strip().str.lower()

    # Create a dictionary to hold the JSON data for individual entries
    json_data = {}

    # Process the main data (first sheet) to create entries
    for idx, row in df_main.iterrows():
        item_key = row.get('itemname', 'Unknown Item').strip() if pd.notna(row.get('itemname')) else 'Unknown Item'
    
        # Handle anonymization of questions if required
        if anonymize:
            description = f"Question {idx }"  # Corrected index to start from 1
        else:
            description = row.get('itemdescription', 'No description available')

        # Skip rows with placeholder 'Unknown Item' or missing values if necessary
        if item_key.lower().startswith("itemname"):
            continue

        # Determine the number of levels from the 'likert_scale' column
        try:
            num_levels = int(row['likert_scale']) if pd.notna(row['likert_scale']) else 0
        except (ValueError, KeyError, TypeError):
            num_levels = 0  # Default to 0 if not specified or invalid
            
                # Check for "open" response option


        # Create entry with the description
        entry = {
            "Description": description
        }

        # Handle levels if likert_scale is greater than 0
        if num_levels > 0:
            levels = {}
            for i in range(num_levels):  # Iterate based on the number of levels defined in 'likert_scale'
                level_col = f'levels.{i}' if i > 0 else 'levels'
                description_col = f'leveldescription.{i}' if i > 0 else 'leveldescription'

                # Add level and description if both exist and are not NaN
                if level_col in df_main.columns and description_col in df_main.columns:
                    if pd.notna(row[level_col]) and pd.notna(row[description_col]):
                        try:
                            level_value = int(row[level_col])  # Assuming numeric level values
                            level_description = row[description_col]
                            levels[str(level_value)] = level_description
                        except (ValueError, TypeError):
                            continue

            # Add levels to the entry only if they exist
            if levels:
                entry["Levels"] = levels
        
                # Check if 'leveldescription' is in the columns of the DataFrame        
        else:
            # Check that 'leveldescription' exists and is not NaN
            if 'leveldescription' in df_main.columns and pd.notna(row['leveldescription']):
                entry["Units"] = str(row['leveldescription']).strip()
                


        # Add entry to the JSON data dictionary
        # json_data[item_key] = entry
        # Clean the key to remove '-' and '_' characters
        clean_key = re.sub(r'[-_]', '', item_key)
        json_data[clean_key] = entry

    # Process the additional metadata (second sheet)
    for _, row in df_taskdescription.iterrows():
        key = row['key name']
        value = row.get('description', '')  # Using the description field as the value (adjust if needed)
        if pd.notna(key) and pd.notna(value):
            json_data[key] = value

    # Process the additional metadata (second sheet)
    for _, row in df_nonlikert.iterrows():
        key = row['key name']
        value = row.get('description', '') 
        # print(f"Value of NonLikert {value}") # Using the description field as the value (adjust if needed)
        if pd.notna(key) and pd.notna(value):
            json_data[key] = value

    # print(f"Length of json data {len(json_data)}")
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
        print(f"JSON data has been written to {output_json_file}")

def create_bids_structure_and_copy_data(session_file, task_name, task_file, output_folder, study_folder):
    """
    Create BIDS structure and copy data.

    Parameters:
    session_file (str): Path to the session file.
    task_name (str): Name of the task.
    task_file (str): Path to the task definition file.
    output_folder (str): Path to the output folder where BIDS structure will be created.
    study_folder (str): Name of the study folder (e.g., PK01).
    """
    logging.debug(f"Loading session data from {session_file}")
    
    # Load session data and normalize column names
    df_session = pd.read_excel(session_file)
    df_session.columns = [normalize_item_name(col) for col in df_session.columns]
    logging.debug(f"Normalized session file columns: {df_session.columns.tolist()}")

    # Ensure 'id' and 'ses' columns exist
    if 'id' in df_session.columns and 'ses' in df_session.columns:
        df_session.rename(columns={'id': 'subject_id', 'ses': 'session'}, inplace=True)
        logging.debug("Renamed 'id' and 'ses' columns to 'subject_id' and 'session'")
    else:
        raise ValueError("The input session file must contain 'id' and 'ses' columns.")

    # Filter task-specific columns
    df_session.columns = [normalize_item_name(col) for col in df_session.columns]
    task_columns = [col for col in df_session.columns if task_name in col]
    logging.debug(f"Task columns found: {task_columns}")

    # Load task definition
    df_task = pd.read_excel(task_file)
    task_item_column = next((col for col in df_task.columns if col.lower() == 'itemname'), None)
    if task_item_column is None:
        raise ValueError("The task definition file must contain a column named 'itemname' (case-insensitive).")
    
    # Normalize task items and filter out invalid entries
    task_items = [normalize_item_name(item) for item in df_task[task_item_column].tolist() if 'example' not in str(item).lower()]
    logging.debug(f"Task items after normalization: {task_items}")
    
    # Check for NaN in task_items
    nan_items = [item for item in task_items if isinstance(item, float) and math.isnan(item)]
    if nan_items:
        logging.error(Fore.RED + f"Found NaN values in task_items: {nan_items}" + Style.RESET_ALL)

    # Check for NaN in task_columns
    nan_columns = [col for col in task_columns if isinstance(col, float) and math.isnan(col)]
    if nan_columns:
        logging.error(Fore.RED + f"Found NaN values in task_columns: {nan_columns}" + Style.RESET_ALL)

    # Check for missing items globally (for debugging purposes)
    missing_items_global = [item for item in task_items if item not in task_columns]
    if missing_items_global:
        logging.debug(Fore.RED + f"The following task items are missing in the session file for task {task_name}: {missing_items_global}" + Style.RESET_ALL)

    # Filter DataFrame
    relevant_columns = ['subject_id', 'session'] + [col for col in task_columns if col in task_items]
    df_filtered = df_session[relevant_columns]
    # logging.debug(f"Filtered DataFrame size: {df_filtered.shape}")

    if df_filtered.shape[1] == 2:
        logging.debug(Fore.RED + f"DataFrame too small to write {task_file}" + Style.RESET_ALL)
    else:
        for row in df_filtered.itertuples(index=False):
            subject_id = row.subject_id
            session = row.session
            logging.debug(f"Processing subject: {subject_id}, session: {session}")

            # Ensure subject_id is formatted correctly
            subject_id = re.sub(r"^sub-+", "sub-", subject_id)
            if not subject_id.startswith("sub-"):
                subject_id = f"sub-{subject_id}"

            # Create session folder
            subject_folder = os.path.join(output_folder, f'{subject_id}')
            session_folder = os.path.join(subject_folder, f'ses-{session}', 'beh')
            os.makedirs(session_folder, exist_ok=True)
            logging.debug(f"Created session folder: {session_folder}")

            # Prepare output filename
            output_file = os.path.join(session_folder, f'{subject_id}_ses-{session}_task-{task_name.lower()}_beh.tsv')
            logging.debug(f"Output file path: {output_file}")

            # Convert row to DataFrame
            row_df = pd.DataFrame([row])

            # Function to convert float to int if possible
            def convert_floats(val):
                if isinstance(val, float) and val.is_integer():
                    return int(val)
                return val

            # Apply conversion to numerical columns only
            row_df = row_df.apply(lambda col: col.map(convert_floats) if col.dtype.kind in 'fi' else col)
            # Remove commas from string columns only
            # Clean string columns: remove commas and new lines
            row_df = row_df.apply(lambda col: col.map(clean_text) if col.dtype == 'object' else col)

            row_df.drop(columns=['subject_id', 'session'], inplace=True)

            # Save as TSV
            row_df.to_csv(output_file, sep='\t', index=False)
            # logging.info(Fore.GREEN + f"Saved {output_file}" + Style.RESET_ALL)

            # Check for missing items for this specific subject and session
            missing_items_subject = [item for item in task_items if item not in task_columns]
            if missing_items_subject:
                logging.warning(Fore.RED + f"Subject {subject_id}, Session {session}: The following task items are missing for task {task_name}: {missing_items_subject}" + Style.RESET_ALL)

def convert_demographics_to_participants(demographics_file, variables_file, output_folder, anonymize=False):
    """
    Creates participants.tsv from a dedicated demographics file, ignoring session files.
    """

    # 1️⃣ Read demographics Excel
    print(f"Loading demographics from: {demographics_file}")
    df_demo = pd.read_excel(demographics_file)
    # Normalize column names (lowercase)
    df_demo.columns = df_demo.columns.str.strip().str.lower()

    # 2️⃣ Read variable definitions from participants_variables.xlsx (sheet 1)
    print(f"Loading variable definitions from: {variables_file}")
    df_variables = pd.read_excel(variables_file, sheet_name=0)  # first sheet
    df_variables['VariableName'] = df_variables['VariableName'].str.strip().str.lower()

    # 3️⃣ Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # 4️⃣ Identify required columns from the variables file
    required_columns = df_variables['VariableName'].tolist()

    # 5️⃣ Check for missing columns in demographics
    missing_columns = [col for col in required_columns if col not in df_demo.columns]
    if missing_columns:
        print(f"⚠️  Missing columns in demographics file: {missing_columns}")
        for col in missing_columns:
            # If the column is truly missing, we either drop or set as 'n/a'
            df_demo[col] = 'n/a'

    # 6️⃣ Extract only columns that exist in demographics
    df_participants = df_demo[required_columns].copy()

    # 7️⃣ Normalize participant ID
    # We assume the column 'id' is the participant identifier
    if 'id' in df_participants.columns:
        def normalize_id(id_value):
            if isinstance(id_value, str):
                if id_value.startswith("sub-"):
                    return id_value
                elif re.match(r"^\d{3,}$", id_value):
                    return f"sub-{id_value}"
            elif isinstance(id_value, int):
                return f"sub-{id_value:03d}"
            return "sub-unknown"

        df_participants['participant_id'] = df_participants['id'].apply(normalize_id)
        # Remove the old 'id' column from the final TSV
        df_participants.drop(columns=['id'], inplace=True)

    # 8️⃣ Move participant_id to the first column
    if 'participant_id' in df_participants.columns:
        cols = df_participants.columns.tolist()
        cols.insert(0, cols.pop(cols.index('participant_id')))
        df_participants = df_participants[cols]

    # 9️⃣ Apply data types based on participants_variables.xlsx
    dtype_map = dict(zip(df_variables['VariableName'], df_variables['DataType'].str.lower()))

    for col in df_participants.columns:
        # skip participant_id
        if col == 'participant_id':
            continue

        if col in dtype_map:
            if dtype_map[col] == 'integer':
                df_participants[col] = pd.to_numeric(df_participants[col], errors='coerce').astype('Int64', errors='ignore')
            elif dtype_map[col] == 'float':
                df_participants[col] = pd.to_numeric(df_participants[col], errors='coerce')
            elif dtype_map[col] == 'cat_num':
                numeric_col = pd.to_numeric(df_participants[col], errors='coerce')
                if numeric_col.notna().all() and (numeric_col % 1 == 0).all():  # all whole numbers
                    df_participants[col] = numeric_col.astype('Int64')
                else:
                    df_participants[col] = df_participants[col].astype(str)
            elif dtype_map[col] == 'cat_string':
                df_participants[col] = df_participants[col].astype(str)
    for col in df_participants.columns:
        if col in dtype_map:
            if dtype_map[col] in ['integer', 'cat_num']:  # Ensure categorical numbers are also treated as integers
                df_participants[col] = pd.to_numeric(df_participants[col], errors='coerce').astype(pd.Int64Dtype())


    # 1️⃣0️⃣ Write participants.tsv
    participants_tsv_path = os.path.join(output_folder, "participants.tsv")
    df_participants.replace(-999, pd.NA, inplace=True)  # Ensure missing values are set to NA

    # Convert all 'Int64' columns to standard Python integers before writing
    for col in df_participants.columns:
        if col in dtype_map:
            if dtype_map[col] == 'integer':
                df_participants[col] = pd.to_numeric(df_participants[col], errors='coerce').astype(pd.Int64Dtype())
 # Replace missing values and convert to int

    df_participants.to_csv(participants_tsv_path, sep='\t', index=False, na_rep='n/a')


    # orig df_participants.to_csv(participants_tsv_path, sep='\t', index=False, na_rep='n/a')
    print(f"✅ Saved participants.tsv at {participants_tsv_path}")

    # 1️⃣1️⃣ Create (optional) participants.json
    participants_json_path = os.path.join(output_folder, 'participants.json')
    participants_json_content = {}

    for idx, row in df_variables.iterrows():
        variable_name = str(row['VariableName']).lower()
        if variable_name == 'id': 
            continue

        description = row.get('Description', '')
        data_type = row.get('DataType', '').lower()
        levels_str = row.get('Levels', '')

        variable_entry = {"Description": description}
        # if data_type:
        #    variable_entry["DataType"] = data_type.capitalize()

        # If 'cat_num' or 'cat_string' have levels, parse them
        if data_type in ['cat_num', 'cat_string'] and pd.notna(levels_str):
            levels = {}
            for level in levels_str.split(';'):
                key_value = level.strip().split(':')
                if len(key_value) == 2:
                    key, val = key_value
                    levels[key.strip()] = val.strip()
            if levels:
                variable_entry["Levels"] = levels

        participants_json_content[variable_name] = variable_entry

    # Add participant_id metadata
    participants_json_content['participant_id'] = {
        "Description": "Unique participant identifier",
        "LongName": "Participant ID"
    }

    with open(participants_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(participants_json_content, json_file, indent=4, ensure_ascii=False)
    print(f"✅ Saved participants.json at {participants_json_path}")
    
        # 🔹 Load dataset description from second sheet
    dataset_description = load_dataset_description(variables_file)

    # 🔹 Save dataset_description.json in the root output folder
    write_dataset_description(dataset_description, output_folder)

def process_all_xlsx_in_folder(folder_path, output_folder, anonymize=False):
    # Iterate over all .xlsx files in the specified folder
    folder_path = os.path.abspath('/resources/')
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xlsx'):
            file_path = os.path.join(folder_path, file_name)
            # Generate output JSON filename based on input filename
            output_file_name = f"task-{os.path.splitext(file_name)[0].lower()}_beh.json"
            output_dir = os.path.join('/bids/rawdata')
            os.makedirs(output_dir, exist_ok=True)
            output_file_path = os.path.join('/bids/rawdata', output_file_name)

            # Convert the Excel file to JSON
            print(f"Processing {file_name}...")
            convert_excel_to_json_updated(file_path, output_file_path, anonymize=anonymize)

def load_dataset_description(variables_file):
    """
    Load the second sheet of participants_variables.xlsx as a dataset description.
    Reads the first column as keys and the second column as values.
    """
    print(f"Loading dataset description from: {variables_file}")

    # Read the second sheet (index 1)
    df_description = pd.read_excel(variables_file, sheet_name=1, header=None)

    # Ensure at least two columns exist (key-value structure)
    if df_description.shape[1] < 2:
        raise ValueError("Dataset description sheet must contain at least two columns (key, value).")

    # Convert first column to keys and second column to values
    dataset_description = dict(zip(df_description.iloc[:, 0].astype(str), df_description.iloc[:, 1].astype(str)))

    print(f"✅ Dataset description loaded: {dataset_description}")
    return dataset_description

def write_dataset_description(dataset_description, output_folder):
    """
    Write dataset description to dataset_description.json in the root folder.
    """
    output_json_file = os.path.join(output_folder, "dataset_description.json")

    print(f"Writing dataset description to file: {output_json_file}")
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(dataset_description, json_file, indent=4, ensure_ascii=False)

    print(f"✅ Dataset description saved to {output_json_file}")

def normalize_item_name(item_name):
    """ 
    Normalize item names by converting the prefix to uppercase 
    only if they end with a number.
    """
    item_name = str(item_name)  # Ensure it's a string
    match = re.match(r'([A-Za-z]+)[\s\-_]?(\d+)$', item_name)  # Match only items ending in a number
    if match:
        return f"{match.group(1).upper()}{match.group(2)}"  # Convert prefix to uppercase
    return item_name  # Return unchanged if it doesn't match

def clean_text(value):
    if isinstance(value, str):  # Ensure we only modify strings
        return re.sub(r'[\n\r,]', ' ', value).strip()  # Replace new lines and commas with space
    return value  # Keep other values unchanged

if __name__ == "__main__":
    print_header()
    main()
