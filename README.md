# 🧠 BEHAVE

## 🧠 What is **BEHAVE**?

**BEHAVE** is a command-line tool that **converts behavioral data from Excel files into BIDS-compliant JSON and TSV files**, making them suitable for neuroimaging data repositories. It takes subject-level behavioral session data and task/questionnaire metadata, and organizes them into the standardized BIDS structure.

To run BEHAVE successfully, the user must prepare:

- A `/data/STUDY_NAME/` folder containing:
  - **Session Excel files** (one per session)
  - A `demographics.xlsx` file with subject-level info
  - A `participants_dataset.xlsx` file with variable definitions and dataset metadata
- A `/resources/` folder containing:
  - **Task definitions** — one `.xlsx` file per behavioral task, each with 3 sheets:
    1. Items & scoring
    2. Task metadata
    3. Non-likert variable definitions

BEHAVE will validate your dataset using the BIDS validator (via `deno`) and output a complete BIDS-formatted `/rawdata/` folder.

------

## 🚀 Quick Start

### ➤ Main Command

```
python behave.py [-h] -d DATA -r RESOURCES -o OUTPUT -s STUDY [--debug]
```

Convert behavioral Excel files into BIDS-compatible `JSON` and `TSV` files.

**Arguments:**

- `-d`, `--data`: Path to the folder containing raw behavioral data.
- `-r`, `--resources`: Path to the resources folder (must contain Excel files like `demographics.xlsx` and `participants_variables.xlsx`).
- `-o`, `--output`: Output folder where BIDS files will be saved.
- `-s`, `--study`: Study name (e.g., `template`).
- `--debug`: Optional. Enables detailed debug logging.
- `-h`, `--help`: Show help message and exit.

------

## 📁 File Format Details (Reference to files on this github repo)

### 🗂 Folder Structure

Ensure your data is organized using the following structure (a sample is included in the repository).

The example folder is named `/data/template`, but you should rename this folder to match your own study ID — for example, `/data/best_study_ever`.

Each session should have its own `sessionX.xlsx` file (`session1.xlsx`, `session2.xlsx`, etc.).
Even for cross-sectional studies with only one session, a `session1.xlsx` file is still required.

> 🔒 **Important:**
> Do **not** rename the following core files — they must always be named exactly as shown:
>
> - `demographics.xlsx`
> - `participants_dataset.xlsx`

These filenames are required by the BEHAVE script to function correctly.

```
behave/
├── data/
│   └── template/
│       ├── session1.xlsx (1 sheets)
│       ├── demographics.xlsx (1 sheets)
│       └── participants_dataset.xlsx (1 sheets)
├── resources/
│   └── testquest.xlsx   ← (task definition with 3 sheets)
```

To successfully run `BEHAVE`, you need the following Excel files organized with specific column structures. Here's what they should look like:

------

### 

The `demographics.xlsx` and `participants_dataset.xlsx` files work together to define participant-level information:

- **`demographics.xlsx`** contains the raw participant data — similar to the `participants.tsv` file in BIDS.

- **`participants_dataset.xlsx`** provides the metadata for each column in `demographics.xlsx`, including variable names, descriptions, and data type (similar to the participants.json)

In short, `demographics.xlsx` holds the data, while `participants_dataset.xlsx` describes and defines it.
### 🧍‍♂️ `demographics.xlsx`

**Location:** `data/STUDY_NAME/demographics.xlsx`

**Purpose:** Provides subject-level information such as age, sex, and group.

**Example Columns:**
First column is required, rest is up to you!

| Column   | Description                        |
| -------- | ---------------------------------- |
| `id`     | Subject ID (e.g., `sub-001`)       |
| `ses`    | Session number (e.g., `1`)         |
| `age`    | Age in years                       |
| `sex`    | Biological sex (coded numerically) |
| `size`   | Height or body size                |
| `weight` | Weight in kilograms                |
| `group`  | Experimental group assignment      |

**Example:**

```
id       ses   age   sex   size   weight   group
sub-001   1     34     2    190     100       2
sub-002   1     20     2    184      80       3
```
------

### 🧾 `participants_dataset.xlsx`

**Location:** `data/STUDY_NAME/participants_dataset.xlsx`

**Purpose:** Defines and describes each participant-level variable. Has two sheets:

#### 📄 Sheet 1 — Variable Definitions

| Column         | Description                                       |
| -------------- | ------------------------------------------------- |
| `VariableName` | Name of the variable (e.g., `age`, `sex`)         |
| `Description`  | Human-readable description of the variable        |
| `DataType`     | Data type (`string`, `integer`, `cat_num`)        |
| `Levels`       | Value mappings for categorical variables (if any) |

**Example:**
```
VariableName   Description           DataType   Levels
id             Participant ID        string
age            Age in years          integer
sex            Biological sex        cat_num    1: Male; 2: Female
```
Note: "cat_num" expects to specify Levels as key:value.

#### 📄 Sheet 2 — Dataset Metadata

| Column            | Example Value |
| ----------------- | ------------- |
| `Name`            | `BIDSVersion` |
| `My Bids dataset` | `1.7.0`       |

Used to auto-generate `dataset_description.json`.

------

### 🧪 `sessionX.xlsx`

**Location:** `data/STUDY_NAME/session1.xlsx`

**Purpose:** Contains item-level responses from a behavioral task.

**Required Columns:**

| Column           | Description                                      |
| ---------------- | ------------------------------------------------ |
| `id`             | Subject ID (`sub-001`, etc.)                     |
| `ses`            | Session number                                   |
| `testquest01...` | One column per task item (e.g., Likert response) |


**Example:**

```
id       ses   testquest01  testquest02  testquest03  ...
sub-001   1           0            1           3
sub-002   1           2            1           2
```

Each item must match a variable defined in the corresponding task file in the `/resources/` folder.

------

## 🧾 Task File Format (`resources/[task].xlsx`)

Each behavioral task should be described using an Excel file inside the `resources/` folder. This file guides how the item-level responses in `sessionX.xlsx` are interpreted.

**Sheet 1** should include the following structure:

| Column Name        | Description                                                  |
| ------------------ | ------------------------------------------------------------ |
| `itemname`         | Unique column name matching those in `sessionX.xlsx` (e.g., `testquest01`) |
| `itemdescription`  | Full question or prompt presented to participants            |
| `likert_scale`     | Number of scale levels (0 if non-likert)                     |
| `levels`           | Response code (e.g., `0`, `1`, `2`, ...)                     |
| `leveldescription` | Text description for each level (must pair with a `levels` value) |

Additional pairs of `levels` and `leveldescription` can be added for multi-scale items.

------

### ✅ Example

**File:** `resources/example_task.xlsx`
**Sheet 1:** (Item Metadata)

| itemname    | itemdescription                                              | likert_scale | levels | leveldescription                          | ...  |
| ----------- | ------------------------------------------------------------ | ------------ | ------ | ----------------------------------------- | ---- |
| testquest01 | I feel confident in my ability to complete tasks at work.    | 4            | 0      | Rarely or none of the time                | ...  |
| testquest02 | I enjoy participating in group discussions and activities.   | 4            | 1      | Some or a little of the time              | ...  |
| testquest03 | I often feel stressed when managing multiple responsibilities. | 4            | 2      | Occasionally or a moderate amount of time | ...  |


ℹ️ You may include additional `levels`/`leveldescription` columns if needed (e.g., for 5-point or alternative scales).

------

### 🔐 Key Rules

- Every `itemname` **must match** a column in `sessionX.xlsx`.
- `likert_scale` defines how many levels exist (e.g., 4 for a 0–3 scale).
- You **must provide matching `levels` and `leveldescription` pairs**.
- If your item is not a Likert scale, set `likert_scale` to `0`.

## 📋 Task Metadata — Sheet 2 (`resources/[task].xlsx`)

**Purpose:** Describes the behavioral task for the BIDS sidecar JSON file (`task-[name]_beh.json`).

This sheet should contain **key-value pairs** that correspond to standard BIDS fields describing behavioral tasks.

| Column Name   | Description                                                  |
| ------------- | ------------------------------------------------------------ |
| `Key name`    | The BIDS-compliant JSON field name (e.g., `TaskName`, `Instructions`) |
| `Description` | Human-readable explanation of the field                      |
| `Data type`   | Expected data type: `string`, `number`, `URI`, etc.          |
| `Info`        | The value to include in the JSON (this is what BEHAVE will extract and write into the `.json` file) |


------

### ✅ Example

| Key name                      | Description                                     | Data type | Info                       |
| ----------------------------- | ----------------------------------------------- | --------- | -------------------------- |
| `TaskName`                    | Name of the task. Becomes part of the filename. | string    | `testquest`                |
| `Instructions`                | Text shown to participants before the task      | string    | `You should be honest...`  |
| `TaskDescription`             | Longer description of the task                  | string    | `Some info about the test` |
| `CogAtlasID`                  | URI for Cognitive Atlas task term               | string    | `Not categorised`          |
| `CogPOID`                     | URI for CogPO term                              | string    | `Not categorised`          |
| `InstitutionName`             | Institution responsible for the task            | string    | `University of Graz`       |
| `InstitutionAddress`          | Address of the institution                      | string    | `Kopernikusgasse`          |
| `InstitutionalDepartmentName` | Department name at the institution              | string    | `MRI Lab Graz`             |

------
### 📌 Tips

- Only **one row per key** is required.
- This information is used to automatically generate the `task-[taskname]_beh.json` file in your BIDS output.
- Task names are sanitized automatically (e.g., `test quest` → `testquest`).
______

### ➤ Additional Tool: `behave_together`

```
python behave_together.py [-h] -b BIDS_DIR -t TASKS [TASKS ...] [--all]
```

Gather behavioral BIDS data across multiple tasks into a single wide CSV.

**Arguments:**

- `-b`, `--bids_dir`: Top-level BIDS directory.
- `-t`, `--tasks`: List of task names to include (e.g., `-t ADS GNG`).
- `--all`: Optional. Automatically gather all tasks found via `task-*_beh.json`.
- `-h`, `--help`: Show help message and exit.

------

# 📦 Installation

## Step 1: Clone the Repository

```
git clone https://github.com/your-username/behave.git
cd behave
```

## Step 2: Set Up the Environment

Run the setup script to create a virtual environment and install required packages:

- **Windows:**

  ```
  uv_setup.bat
  ```

- **macOS/Linux:**

  ```
  ./uv_setup.sh
  ```

## Step 3: Activate the Environment

```
source .behave/bin/activate
```

To deactivate later:

```
deactivate
```

------

## 🧰 Requirements

Ensure Python 3.8+ is installed.

The following Python packages will be installed automatically via the setup script:

- `pandas` – Data manipulation
- `openpyxl` – Excel reading
- `numpy` – Numerical operations
- `colorama` *(optional)* – Colored terminal output

**Standard libraries used** (no installation needed):

- `os`, `json`, `logging`, `re`

------

## ✅ Manual `uv` Installation (Windows Only)

If `uv` is not yet installed, follow these steps:

### 1. Download `uv`

Go to the [uv releases page](https://github.com/astral-sh/uv/releases) and download:

```
uv-x86_64-pc-windows-msvc.zip
```

### 2. Extract the ZIP

Extract it to:

```
C:\Users\YourUsername\Programs\uv\
```

You should now have `uv.exe` in that folder.

### 3. Add to PATH

- Open **Environment Variables** via system settings.

- Edit your `Path` under **User variables**.

- Add:

  ```
  C:\Users\YourUsername\Programs\uv\
  ```

### 4. Verify Installation

Open a new terminal and run:

```
uv --version
```

You should see the version number printed.
