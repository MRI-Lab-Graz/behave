# 🧠 BEHAVE

**Convert (any) behavioral data into BIDS format.**

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

## 📦 Installation

### Step 1: Clone the Repository

```
git clone https://github.com/your-username/behave.git
cd behave
```

### Step 2: Set Up the Environment

Run the setup script to create a virtual environment and install required packages:

- **Windows:**

  ```
  uv_setup.bat
  ```

- **macOS/Linux:**

  ```
  ./uv_setup.sh
  ```

### Step 3: Activate the Environment

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
