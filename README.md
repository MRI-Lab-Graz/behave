# BEHAVE

Converting (any) behavioural data into BIDS

## What you need to know

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



![Drag Racing](LOGO.png)
