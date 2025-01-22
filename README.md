# A very simple script that generates a PDF for Paperless ASN-Codes with QR code from numbers that are loaded from the CSV file.

### The script is written in Python and uses the fpdf library for the PDF generation.
### An attempt is always made to automatically create full sheets as required.

The parameters for the labels can be adjusted in config.py.
The settings should be suitable for Herma labels with the number 10916.


![image](https://github.com/user-attachments/assets/acd627b9-557c-4287-b997-8e995289e309)

After the CSV file has been loaded, the data is analyzed and displayed as info.
A print area can now be specified to filter the data.
If no range is defined, all data is written to the PDF.
Limits can be set for Start and End Value.
Only numbers are valid as limits.

For example, if 800 is specified as the start and 1100 as the end, 
the program reports that there are 301 lables and suggests extending it to 336 to fill an entire sheet.

The data that has been write in a pdf lables_[timestamp].pdf alabes can be deleted from the CSV file using the checkbox.
However, a backup file is created.

## Installation

1. Create a folder to save the scripts and virtual environment `mkdir scripts`
2. cd into scripts directory `cd scripts`
3. Create a virtual environment `python -m venv venv`
4. Activate the virtual environment using one of the commands below

```
source venv/bin/activate
. ./venv/bin/activate` 
```
5. Install the dependencies `pip install -r requirements.txt`
6. Clone this repository to the directory
   
   

