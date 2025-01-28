import pandas as pd
import json

NO_DESCRIPTION = 'No description available'

def load_excel_sheets(excel_file):
    print(f"Loading Excel file: {excel_file}")
    df_main = pd.read_excel(excel_file, sheet_name=0, skiprows=0)
    df_additional = pd.read_excel(excel_file, sheet_name=1)
    df_main.columns = df_main.columns.str.strip().str.lower()
    df_additional.columns = df_additional.columns.str.strip().str.lower()
    print("Excel sheets loaded successfully.")
    return df_main, df_additional

def process_main_data(df_main, anonymize):
    print("Processing main data...")
    json_data = {}
    for idx, row in df_main.iterrows():
        if idx < 1:  # Skip the first row (header)
            continue
        if idx == 1:
            likert_scale_columns = [col for col in df_main.columns if 'likert_scale' in col.lower()]
        item_key = row.get('itemname')
        likert_scale_value = row.get('likert_scale')
        description = row.get('itemdescription', NO_DESCRIPTION)
        if pd.notna(likert_scale_value):
            try:
                num_levels = int(float(likert_scale_value))
                print(f"Likert scale value for {item_key} is {num_levels}")  # Debugging output
            except ValueError:
                num_levels = 0
                print(f"Invalid likert scale value for {item_key}, setting num_levels to 0")  # Debugging output
        else:
            num_levels = 0
        
        print(f"Processing item: {item_key} with {num_levels} levels")
        entry = {"Description": description}
        if num_levels > 0:
            levels = {}
            for i in range(num_levels):
                level_index = 2 * i
                level_col = row.iloc[level_index + 2]  # Adjusted index to skip initial columns
                description_col = row.iloc[level_index + 3]  # Adjusted index to skip initial columns
                if pd.notna(level_col) and pd.notna(description_col):
                    try:
                        level_value = int(level_col)
                        level_description = description_col
                        levels[str(level_value)] = level_description
                        print(f"Level {level_value}: {level_description}")  # Debugging output
                    except (ValueError, TypeError):
                        continue
            entry["Levels"] = levels
        json_data[item_key] = entry
    print("Main data processed successfully.")
    return json_data

def process_additional_data(df_additional, json_data):
    print("Processing additional data...")
    for idx, row in df_additional.iterrows():
        if idx < 1:  # Skip the first row (header)
            continue
        key = row.get('key name')
        value = row.get('description', '')
        if pd.notna(key) and pd.notna(value):
            json_data[key] = value
    print("Additional data processed successfully.")

def write_json_file(json_data, output_json_file):
    print(f"Writing JSON data to file: {output_json_file}")
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
        print(f"JSON data has been written to {output_json_file}")
