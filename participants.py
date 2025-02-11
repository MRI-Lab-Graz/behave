import os
import re
import json
import pandas as pd

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
                df_participants[col] = pd.to_numeric(df_participants[col], errors='coerce').astype('Int64')
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

    # 1️⃣0️⃣ Write participants.tsv
    participants_tsv_path = os.path.join(output_folder, "participants.tsv")
    df_participants.to_csv(participants_tsv_path, sep='\t', index=False, na_rep='n/a')
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
        if data_type:
            variable_entry["DataType"] = data_type.capitalize()

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
