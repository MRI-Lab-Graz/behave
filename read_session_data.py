import pandas as pd
import os
import logging
from colorama import Fore, Style, init
import re

# Initialize colorama
init(autoreset=True)

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


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_bids_structure_and_copy_data(session_file, task_name, task_file, output_folder):
    """
    Create BIDS structure and copy data.

    Parameters:
    session_file (str): Path to the session file.
    task_name (str): Name of the task.
    task_file (str): Path to the task definition file.
    output_folder (str): Path to the output folder where BIDS structure will be created.
    """
    
    logging.debug(f"Loading session data from {session_file}")
    # Load session data and normalize column names
    df_session = pd.read_excel(session_file)
    df_session.columns = [normalize_item_name(col) for col in df_session.columns]
    logging.debug(f"Normalized session file columns: {df_session.columns.tolist()}")

    logging.debug(f"Session data loaded with columns: {df_session.columns.tolist()}")

    # Ensure 'id' and 'ses' columns exist
    if 'id' in df_session.columns and 'ses' in df_session.columns:
        df_session.rename(columns={'id': 'subject_id', 'ses': 'session'}, inplace=True)
        logging.debug("Renamed 'id' and 'ses' columns to 'subject_id' and 'session'")
    else:
        raise ValueError("The input session file must contain 'id' and 'ses' columns.")

    # Filter task-specific columns
    # Normalize column names
    df_session.columns = [normalize_item_name(col) for col in df_session.columns]

    # Extract task-relevant columns
    task_columns = [col for col in df_session.columns if task_name in col]
    logging.debug(f"Normalized task columns found: {task_columns}")


    logging.debug(f"Task columns found: {task_columns}")

    # Load task definition
    df_task = pd.read_excel(task_file)
    task_item_column = next((col for col in df_task.columns if col.lower() == 'itemname'), None)
    if task_item_column is None:
        raise ValueError("The task definition file must contain a column named 'itemname' (case-insensitive).")
    
    task_items = [normalize_item_name(item) for item in df_task[task_item_column].tolist()]

    logging.debug(f"Task items loaded: {task_items}")

    missing_items = [item for item in task_items if item not in task_columns]
    if missing_items:
        logging.warning(Fore.RED + f"The following task items are missing in the session file: {missing_items}")

    # Filter DataFrame
    relevant_columns = ['subject_id', 'session'] + [col for col in task_columns if col in task_items]
    df_filtered = df_session[relevant_columns]
    logging.debug(f"Filtered DataFrame size: {df_filtered.shape}")

    if df_filtered.shape[1] == 2:
        logging.info(Fore.RED + f"DataFrame too small to write {task_file}" + Style.RESET_ALL)
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
            #subject_folder = os.path.join(output_folder, 'bids', 'rawdata', f'{subject_id}')
            subject_folder = os.path.join('bids', 'rawdata', f'{subject_id}')
            session_folder = os.path.join(subject_folder, f'ses-{session}', 'beh')
            os.makedirs(session_folder, exist_ok=True)
            # logging.debug(f"Created directories: {session_folder}")

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

            # Save as TSV
            row_df.to_csv(output_file, sep='\t', index=False)

            logging.info(Fore.GREEN + f"Saved {output_file}" + Style.RESET_ALL)
