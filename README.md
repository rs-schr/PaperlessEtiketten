<b>A very simple script that generates a PDF with QR codes from ASN numbers that are loaded from the CSV file.</b>

The parameters for the labels can be adjusted in config.py.

![image](https://github.com/user-attachments/assets/acd627b9-557c-4287-b997-8e995289e309)

After the CSV file has been loaded, the range contained in the file is output.
If no range is defined, all data is written to the PDF.
Limits can be set for Start and End Value.
Only numbers are valid as limits.

For example, if 800 is specified as the start and 1100 as the end, 
the program reports that there are 301 labels and suggests extending it to 336 to fill an entire sheet.
