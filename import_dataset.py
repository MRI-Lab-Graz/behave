import pandas as pd
import json
import os

def convert_excel_to_json_updated(excel_file, output_json_file, anonymize=False):
    # Load both sheets from the Excel file
    df_main = pd.read_excel(excel_file, sheet_name=0, skiprows=0)

    # Ensure the base directory for the output JSON file exists
    output_dir = os.path.dirname(output_json_file)
    print(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    df_taskdescription = pd.read_excel(excel_file, sheet_name=1)
    df_nonlikert = pd.read_excel(excel_file, sheet_name=2)

    # Clean up column names (strip whitespace and convert to lowercase) for the main data
    df_main.columns = df_main.columns.str.strip().str.lower()
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

        # Add entry to the JSON data dictionary
        json_data[item_key] = entry

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
        print(f"Value of NonLikert {value}") # Using the description field as the value (adjust if needed)
        if pd.notna(key) and pd.notna(value):
            json_data[key] = value

    print(f"Length of json data {len(json_data)}")
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
        print(f"JSON data has been written to {output_json_file}")

    

def process_all_xlsx_in_folder(folder_path, output_folder, anonymize=False):
    # Iterate over all .xlsx files in the specified folder
    folder_path = os.path.abspath('./resources/')
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xlsx'):
            file_path = os.path.join(folder_path, file_name)
            # Generate output JSON filename based on input filename
            output_file_name = f"task-{os.path.splitext(file_name)[0].lower()}_beh.json"
            output_dir = os.path.join('./bids/rawdata')
            os.makedirs(output_dir, exist_ok=True)
            output_file_path = os.path.join('./bids/rawdata', output_file_name)

            # Convert the Excel file to JSON
            print(f"Processing {file_name}...")
            convert_excel_to_json_updated(file_path, output_file_path, anonymize=anonymize)