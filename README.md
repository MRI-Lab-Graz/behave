# BEHAVE

Converting (any) behavioural data into BIDS

## behave

````bash
python behave.py [-h] -d DATA -r RESOURCES -o OUTPUT -s STUDY [--debug]
````

Process data and resources folders to convert Excel files into JSON and TSV formats. This script expects specific Excel files in the resources
folder: - 'demographics.xlsx' for demographic data - 'participants_variables.xlsx' for variable definitions and dataset descriptions.

Options: 
* -h, --help: show this help message and exit
* -d DATA, --data DATA : Path to the data folder where input files will are saved.
* -r RESOURCES, --resources RESOURCES: Path to the resources folder containing input Excel files.
* -o OUTPUT, --output OUTPUT: Path to the BIDS-output folder.
* -s STUDY, --study STUDY: Study name (e.g., template)
* --debug: Enable debug logging

## behave_together
Gather BIDS behavioral data across multiple tasks into one wide CSV.

options:
* -h, --help: show this help message and exit
* -b BIDS_DIR, --bids_dir BIDS_DIR: Path to the top-level BIDS directory.
* -t TASKS [TASKS ...], --tasks TASKS [TASKS ...]: Task name(s) to gather (e.g., '-t ADS GNG').
* --all: Gather data for ALL tasks found via task-*_beh.json in the BIDS root.

## Requirements

The following Python packages need to be installed on the target PC. These packages are used in the script and are not part of Python's standard library. You can install them using pip:

* pandas: For data manipulation and handling dataframes.
* openpyxl: For reading Excel files (.xlsx).
* numpy: Often used by pandas for numerical operations.
* os: Standard library module, no need to install.
* logging: Standard library module, no need to install.
* json: Standard library module, no need to install.
* re: Standard library module, no need to install.
* colorama (optional): If you use Fore.RED or similar, you need this for colored terminal output.

Command to install the required packages:

````bash
pip install pandas openpyxl numpy colorama
````

Additionally, ensure that Python (3.6 or higher) is installed on the target PC.

![Drag Racing](LOGO.png)
