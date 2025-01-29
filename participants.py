import pandas as pd
import json
import os
import re

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


def convert_excel_to_participants(df_session, variables_file, output_folder, anonymize=False):
    # Clean up session data column names
    df_session.columns = df_session.columns.str.strip().str.lower()
    
    # Load variable definitions
    df_variables = pd.read_excel(variables_file)
    df_variables['VariableName'] = df_variables['VariableName'].str.strip().str.lower()
    
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Prepare participants.tsv data
    required_columns = df_variables['VariableName'].tolist()
    
    # Check for required columns in session data
    missing_columns = [col for col in required_columns if col not in df_session.columns]
    if missing_columns:
        print(f"Missing columns in session data: {missing_columns}")
        for col in missing_columns:
            df_session[col] = 'n/a'
    
    # Extract required columns
    df_participants = df_session[required_columns].copy()

    # 🔹 Map variable names to their declared data types
    dtype_map = dict(zip(df_variables['VariableName'], df_variables['DataType'].str.lower()))

    # Normalize `id` column to ensure proper `sub-XXX` format
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
    df_participants.drop(columns=['id'], inplace=True)

    # Move participant_id to first column
    cols = df_participants.columns.tolist()
    cols.insert(0, cols.pop(cols.index('participant_id')))
    df_participants = df_participants[cols]

    for col in df_participants.columns:
        if col in dtype_map:
            if (dtype_map[col] == 'integer') or (dtype_map[col] == 'cat_num'):
                df_participants[col] = pd.to_numeric(df_participants[col], errors='coerce').astype('Int64')  # Keep as integer
            elif dtype_map[col] == 'float':
                df_participants[col] = pd.to_numeric(df_participants[col], errors='coerce')  # Keep as float # Save as integertreat as string
            elif dtype_map[col] == 'cat_string':  # Categorical strings
                df_participants[col] = df_participants[col].astype(str)  # Always save as string



    # Save participants.tsv
    participants_tsv_path = os.path.join(output_folder, 'participants.tsv')
    df_participants.to_csv(participants_tsv_path, sep='\t', index=False, na_rep='n/a')
    print(f"✅ Saved participants.tsv at {participants_tsv_path}")

    # Prepare participants.json data
    participants_json_content = {}
    for idx, row in df_variables.iterrows():
        variable_name = row['VariableName']

        if variable_name == 'id':
            continue

        description = row.get('Description', '')
        data_type = row.get('DataType', '').lower()
        levels_str = row.get('Levels', '')
        
        variable_entry = {"Description": description}
        
        if data_type:
            variable_entry["DataType"] = data_type.capitalize()
        
        if data_type == 'categorical' and pd.notna(levels_str):
            levels = {}
            for level in levels_str.split(';'):
                key_value = level.strip().split(':')
                if len(key_value) == 2:
                    key, value = key_value
                    levels[key.strip()] = value.strip()
            if levels:
                variable_entry["Levels"] = levels
        
        participants_json_content[variable_name] = variable_entry
    
    # Add participant_id metadata
    participants_json_content['participant_id'] = {
        "Description": "Unique participant identifier",
        "LongName": "Participant ID"
    }
    
    # Save participants.json
    participants_json_path = os.path.join(output_folder, 'participants.json')
    with open(participants_json_path, 'w') as json_file:
        json.dump(participants_json_content, json_file, indent=4)
    print(f"✅ Saved participants.json at {participants_json_path}")

    # 🔹 Load dataset description from second sheet
    dataset_description = load_dataset_description(variables_file)

    # 🔹 Save dataset_description.json in the root output folder
    write_dataset_description(dataset_description, output_folder)