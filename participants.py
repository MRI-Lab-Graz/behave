import pandas as pd
import json
import os
import re 

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
        # Fill missing columns with 'n/a'
        for col in missing_columns:
            df_session[col] = 'n/a'
    
    # Extract required columns
    df_participants = df_session[required_columns].copy()
    
      # Normalize `id` column to ensure proper `sub-XXX` format
    def normalize_id(id_value):
        if isinstance(id_value, str):
            if id_value.startswith("sub-"):  # Already has the prefix
                return id_value
            elif re.match(r"^\d{3,}$", id_value):  # Only numeric (e.g., 001 or 1292001)
                return f"sub-{id_value}"
        elif isinstance(id_value, int):  # If it's an integer
            return f"sub-{id_value:03d}"  # Format with leading zeros
        return "sub-unknown"  # Default for invalid/missing IDs

    
    df_participants['participant_id'] = df_participants['id'].apply(normalize_id)
    df_participants.drop(columns=['id'], inplace=True)
    
    # Move participant_id to first column
    cols = df_participants.columns.tolist()
    cols.insert(0, cols.pop(cols.index('participant_id')))
    df_participants = df_participants[cols]
    
    # Save participants.tsv
    participants_tsv_path = os.path.join(output_folder, 'participants.tsv')
    df_participants.to_csv(participants_tsv_path, sep='\t', index=False, na_rep='n/a')
    print(f"Saved participants.tsv at {participants_tsv_path}")
    
    # Prepare participants.json data
    participants_json_content = {}
    for idx, row in df_variables.iterrows():
        variable_name = row['VariableName']
        description = row.get('Description', '')
        data_type = row.get('DataType', '').lower()
        levels_str = row.get('Levels', '')
        
        variable_entry = {
            "Description": description
        }
        
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
    print(f"Saved participants.json at {participants_json_path}")
