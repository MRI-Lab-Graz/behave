# BEHAVE

Converting (any) behavioural data into BIDS
##
- Check if UV and deno are installed on your local machine (see windows installation below)
- Clone this repository
- Run uv_setup.bat/sh. This will create a virtual environment (.behave) and instsall all necessary pyhton packages.
- When using behave, activate the envirionmant (source .behave/bin/activate)
- When finished deactivat it agein (just type: deactivate)
## ✅ Manual `uv` Installation — **Windows**

### Step 1: Download `uv`

1. Go to the [uv GitHub releases page](https://github.com/astral-sh/uv/releases).
2. Find the latest release.
3. Under **Assets**, download the file:
   - `uv-x86_64-pc-windows-msvc.zip`

### Step 2: Extract the Archive

1. Right-click the downloaded `.zip` file.

2. Select **Extract All**.

3. Extract it to a folder like:

   ```
   C:\Users\YourUsername\Programs\uv\
   ```

You should now have a file called `uv.exe` in that folder.

### Step 3: Add to System `PATH`

1. Press **Win + S**, search for **"Environment Variables"**, and open:

   > “Edit the system environment variables”

2. In the System Properties window, click **Environment Variables…**

3. Under **User variables**, find `Path`, select it, and click **Edit**.

4. Click **New**, then paste:

   ```
   C:\Users\YourUsername\Programs\uv\
   ```

5. Click **OK** through all dialogs.

### Step 4: Test Installation

Open a new PowerShell or CMD window, and run:

```
uv --version
```

You should see the version number, confirming it's installed correctly.

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


Additionally, ensure that Python (3.8 or higher) is installed on the target PC.

![Drag Racing](LOGO.png)
