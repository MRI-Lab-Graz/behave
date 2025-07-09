# BEHAVE - Behavioral Data to BIDS Converter

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![BIDS](https://img.shields.io/badge/BIDS-1.8.0-orange.svg)](https://bids.neuroimaging.io/)

A modular command-line tool that converts behavioral survey data from Excel files into BIDS-compliant JSON and TSV files for neuroimaging data repositories.

![BEHAVE Logo](LOGO.png)

## 🎯 Features

- **📊 Excel to BIDS Conversion**: Automatically converts Excel survey data to BIDS format
- **🧩 Modular Architecture**: Clean separation of concerns across multiple modules
- **✅ Data Validation**: Comprehensive validation of input data and BIDS compliance
- **📝 Flexible Demographics**: Support for complex demographic data with custom data types
- **🏷️ Multiple Data Types**: Handles Likert scales, categorical data, and free-text responses
- **🔧 Robust Error Handling**: Detailed logging and error reporting
- **📦 Single-File Option**: Combined version for easy deployment
- **🚀 Fast Setup**: Quick installation with uv package manager

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Excel File Format](#excel-file-format)
- [BIDS Output](#bids-output)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Option 1: Quick Setup with uv (Recommended)

The fastest way to get started is using our setup script with [uv](https://github.com/astral-sh/uv):

```bash
# Clone the repository
git clone https://github.com/your-username/behave.git
cd behave

# Run the setup script (creates virtual environment and installs dependencies)
chmod +x uv_setup.sh
./uv_setup.sh

# Activate the environment
source .behave/bin/activate  # On Linux/macOS
# or
.behave\Scripts\activate     # On Windows
```

### Option 2: Manual Installation with pip

```bash
# Clone the repository
git clone https://github.com/your-username/behave.git
cd behave

# Create virtual environment
python -m venv .behave
source .behave/bin/activate  # On Linux/macOS
# or
.behave\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Single File Usage

For simple deployment, you can use the combined version without installation:

```bash
# Download just the combined file
wget https://raw.githubusercontent.com/your-username/behave/main/behave_combined.py

# Install dependencies
pip install pandas openpyxl

# Run directly
python behave_combined.py --help
```

## ⚡ Quick Start

```bash
# Convert behavioral data to BIDS format
python behave.py -d data -r resources -o output -s StudyName --debug

# Using the single-file version
python behave_combined.py StudyName /path/to/data /path/to/output --debug
```

## 📖 Usage

### Modular Version

```bash
python behave.py [OPTIONS]

Options:
  -d, --data PATH        Path to data folder containing session files
  -r, --resources PATH   Path to resources folder with questionnaire definitions
  -o, --output PATH      Path to output folder for BIDS data
  -s, --study TEXT       Study identifier (e.g., "StudyXYZ")
  --debug               Enable debug logging
  --anonymize           Anonymize question descriptions
  --skip-validation     Skip BIDS validation
  --log-file PATH       Log to file instead of console
  -h, --help            Show help message
```

### Single-File Version

```bash
python behave_combined.py STUDY_NAME DATA_PATH OUTPUT_PATH [OPTIONS]

Arguments:
  STUDY_NAME    Name of the study
  DATA_PATH     Path to data folder
  OUTPUT_PATH   Path to output folder

Options:
  --debug       Enable debug logging
  --anonymize   Anonymize question names
  -h, --help    Show help message
```

## 📁 File Structure

```
your-project/
├── data/
│   └── StudyName/
│       ├── demographics.xlsx          # Participant demographics
│       ├── participants_dataset.xlsx  # Variable definitions
│       └── session1.xlsx              # Session data files
├── resources/
│   ├── questionnaire1.xlsx           # Task definitions
│   └── questionnaire2.xlsx
└── output/
    └── StudyName/
        └── rawdata/                   # BIDS output folder
            ├── participants.tsv
            ├── participants.json
            ├── dataset_description.json
            ├── task-questionnaire1_beh.json
            └── sub-001/
                └── ses-1/
                    └── beh/
                        └── sub-001_ses-1_task-questionnaire1_beh.tsv
```

## 📊 Excel File Format

### 1. Demographics File (`demographics.xlsx`)

Contains participant demographic information:

| id  | age | gender | education | ... |
|-----|-----|--------|-----------|-----|
| 001 | 25  | 1      | 3         | ... |
| 002 | 32  | 2      | 2         | ... |

### 2. Variables Definition File (`participants_dataset.xlsx`)

**Sheet 1: Variable Definitions**
| VariableName | DataType   | Description | Levels |
|-------------|------------|-------------|---------|
| age         | integer    | Age in years |        |
| gender      | cat_num    | Gender      | 1:Male; 2:Female; 3:Other |
| education   | cat_num    | Education level | 1:High School; 2:Bachelor; 3:Master |

**Sheet 2: Dataset Description**
| Key | Value |
|-----|-------|
| Name | My BIDS Dataset |
| BIDSVersion | 1.8.0 |
| DatasetType | raw |
| Authors | John Doe; Jane Smith |
| License | CC0 |

### 3. Session Files (`session1.xlsx`, etc.)

Contains responses for all participants:

| id  | ses | QUESTIONNAIRE1_item1 | QUESTIONNAIRE1_item2 | ... |
|-----|-----|---------------------|---------------------|-----|
| 001 | 1   | 3                   | 5                   | ... |
| 002 | 1   | 2                   | 4                   | ... |

### 4. Questionnaire Definition Files (`questionnaire1.xlsx`, etc.)

**Sheet 1: Items**
| itemname | itemdescription | likert_scale | levels | leveldescription | levels.1 | leveldescription.1 |
|----------|----------------|--------------|--------|------------------|----------|-------------------|
| item1    | How do you feel? | 5 | 1 | Very bad | 2 | Bad |
| item2    | Rate your mood  | 5 | 1 | Very low | 2 | Low |

**Sheet 2: Task Description**
| key name | description |
|----------|-------------|
| TaskName | Mood Assessment |
| Instructions | Please rate how you feel |

**Sheet 3: Non-Likert Items**
| key name | description |
|----------|-------------|
| ResponseTime | Response time in milliseconds |
| Notes | Additional notes |

## 📋 BIDS Output

The tool generates a complete BIDS-compliant dataset:

### `participants.tsv`
```
participant_id	age	gender	education
sub-001	25	1	3
sub-002	32	2	2
```

### `participants.json`
```json
{
    "participant_id": {
        "Description": "Unique participant identifier"
    },
    "age": {
        "Description": "Age in years"
    },
    "gender": {
        "Description": "Gender",
        "Levels": {
            "1": "Male",
            "2": "Female", 
            "3": "Other"
        }
    }
}
```

### `task-questionnaire1_beh.json`
```json
{
    "item1": {
        "Description": "How do you feel?",
        "Levels": {
            "1": "Very bad",
            "2": "Bad",
            "3": "Neutral",
            "4": "Good", 
            "5": "Very good"
        }
    }
}
```

### `sub-001_ses-1_task-questionnaire1_beh.tsv`
```
item1	item2	item3
3	5	2
```

## ⚙️ Configuration

The tool can be configured through the `config.py` module:

```python
@dataclass
class BehaveConfig:
    # File requirements
    min_required_sheets: int = 3
    
    # Data processing
    anonymize_questions: bool = False
    missing_value_replacement: str = 'n/a'
    missing_value_code: int = -999
    
    # BIDS settings
    bids_version: str = "1.8.0"
```

## 💡 Examples

### Example 1: Basic Conversion

```bash
# Convert a simple study
python behave.py \
    --data ./data \
    --resources ./resources \
    --output ./bids_output \
    --study "PilotStudy" \
    --debug
```

### Example 2: With Anonymization

```bash
# Anonymize question descriptions
python behave.py \
    -d ./data \
    -r ./resources \
    -o ./output \
    -s "Study001" \
    --anonymize \
    --log-file conversion.log
```

### Example 3: Single File Version

```bash
# Using the combined version
python behave_combined.py "MyStudy" ./data ./output --debug
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: `"delimiter" must be a 1-character string`
**Solution**: This was a bug in earlier versions. Update to the latest version.

**Issue**: Missing required Excel sheets
**Solution**: Ensure your questionnaire files have at least 3 sheets (items, task description, non-likert).

**Issue**: BIDS validation errors
**Solution**: Check that all required fields are present in your dataset description.

### Debug Mode

Always use `--debug` flag for detailed logging:

```bash
python behave.py --debug [other options]
```

### Log Files

Save logs to file for later analysis:

```bash
python behave.py --log-file conversion.log [other options]
```

## 📋 Requirements

- Python 3.8+
- pandas >= 1.3.0
- openpyxl >= 3.0.0
- colorama (for colored terminal output)

## 🏗️ Architecture

The tool is built with a modular architecture:

- **`config.py`**: Configuration and constants
- **`excel_handler.py`**: Excel file loading and processing
- **`validators.py`**: Data validation and BIDS compliance
- **`bids_converter.py`**: Main conversion logic
- **`behave.py`**: Main orchestrator script
- **`behave_combined.py`**: Single-file version

## 🧪 Testing

```bash
# Run with test data
python behave.py \
    --data ./data/template \
    --resources ./resources \
    --output ./test_output \
    --study "TestStudy" \
    --debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/your-username/behave.git
cd behave
./uv_setup.sh
source .behave/bin/activate
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MRI-Lab Graz** - Original development
- **BIDS Community** - For the BIDS specification
- **Contributors** - For improvements and bug fixes

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-username/behave/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/your-username/behave/discussions)
- 📧 **Email**: your-email@example.com

## 🔗 Related Projects

- [BIDS Specification](https://bids.neuroimaging.io/)
- [BIDS Validator](https://github.com/bids-standard/bids-validator)
- [pybids](https://github.com/bids-standard/pybids)

---

Made with ❤️ by the MRI-Lab Graz team
