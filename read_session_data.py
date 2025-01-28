import pandas as pd
import os
import logging
from colorama import Fore, Style, init
import re

# Initialize colorama
init(autoreset=True)

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
    # Load the session data
    df_session = pd.read_excel(session_file)
    logging.debug(f"Session data loaded with columns: {df_session.columns.tolist()}")

    # Ensure 'id' and 'ses' columns exist and rename for BIDS compatibility
    if 'id' in df_session.columns and 'ses' in df_session.columns:
        df_session.rename(columns={'id': 'subject_id', 'ses': 'session'}, inplace=True)
        logging.debug("Renamed 'id' and 'ses' columns to 'subject_id' and 'session'")
    else:
        raise ValueError("The input session file must contain 'id' and 'ses' columns.")

    # Filter columns related to the specified task (e.g., ADS)
    task_columns = [col for col in df_session.columns if task_name.lower() in col.lower()]
    logging.debug(f"Task columns found: {task_columns}")

    # Load the task items from the task definition file
    df_task = pd.read_excel(task_file)
    # Find the column name for task items in a case-insensitive manner
    task_item_column = next((col for col in df_task.columns if col.lower() == 'itemname'), None)
    if task_item_column is None:
        raise ValueError("The task definition file must contain a column named 'itemname' (case-insensitive).")
    
    task_items = df_task[task_item_column].tolist()
    logging.debug(f"Task items loaded: {task_items}")

    # Check if all task items are present in the session file
    missing_items = [item for item in task_items if item not in task_columns]
    if missing_items:
        logging.warning(Fore.RED + f"The following task items are missing in the session file: {missing_items}")
    else:
        logging.debug("All task items are present in the session file.")

    # Filter the session DataFrame to include only the relevant task items
    relevant_columns = ['subject_id', 'session'] + [col for col in task_columns if col in task_items]
    df_filtered = df_session[relevant_columns]
    logging.debug(f"Filtered DataFrame for task items: {df_filtered.columns.tolist()}")
    logging.debug(f"Filtered DataFrame size: {df_filtered.shape}")

    
    if df_filtered.shape[1] == 2:
        logging.info(Fore.RED + f"DataFrame too small to write {task_file}" + Style.RESET_ALL)
    else: # Iterate over each row (subject) in the filtered DataFrame
        for row in df_filtered.itertuples(index=False):
            subject_id = row.subject_id
            session = row.session
            logging.debug(f"Processing subject: {subject_id}, session: {session}")

            # Use regex to ensure proper 'sub-XXX' format
            subject_id = re.sub(r"^sub-+", "sub-", subject_id)  # Replace multiple 'sub-' with a single 'sub-'

            # If it still doesn't start with 'sub-', add the prefix
            if not subject_id.startswith("sub-"):
                subject_id = f"sub-{subject_id}"
             

            # Create the folder structure for the subject and session
            subject_folder = os.path.join(output_folder, 'bids', 'rawdata', f'{subject_id}')
            session_folder = os.path.join(subject_folder, f'ses-{session}', 'beh')
            os.makedirs(session_folder, exist_ok=True)
            logging.debug(f"Created directories: {session_folder}")

            # Prepare the output file name
            output_file = os.path.join(session_folder, f'sub-{subject_id}_ses-{session}_task-{task_name.lower()}_beh.tsv')
            logging.debug(f"Output file path: {output_file}")

            # Save the row as a single-line TSV file
            row_df = pd.DataFrame([row])
            row_df.to_csv(output_file, sep='\t', index=False)
            logging.info(Fore.GREEN + f"Saved {output_file}" + Style.RESET_ALL)