# SECTION 1: CONNECTING TO SPREADSHEET AND DOWNLOADING ALL PDF FILES FROM A GOOGLE DRIVE FOLDER

import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

# === SETTING UP ===
# Path to the service account JSON file used for authentication with Google APIs.
SERVICE_ACCOUNT_FILE = 'C:/Users/Gustavo Cunha/Downloads/wired-height-451613-b4-40d0526c8cdc.json'

# Scopes define the level of access the application has to Google Sheets and Google Drive.
SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.file']

# === CONNECTION AND AUTHENTICATION WITH GOOGLE SHEETS ===
# Authenticate using the service account credentials and authorize the client for Google Sheets.
credentials_sheets = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES_SHEETS)
client = gspread.authorize(credentials_sheets)

# Open the spreadsheet using its unique ID (the URL method did not work due to [reason]).
spreadsheet = client.open_by_key('1rzekD9oi277hQf2kQqXfbP8kVB8pUB8X3qjy_IRGYkI')
# Access the specific worksheet (tab) within the spreadsheet.
worksheet = spreadsheet.worksheet('Copy of 110-3b_AB_2024_OCCU_9357_PERS_CCRD')

print("SUCCESSFULLY CONNECTED TO SPREADSHEET!")

# === CONNECTION AND AUTHENTICATION WITH GOOGLE DRIVE ===
# Authenticate using the service account credentials and authorize the client for Google Drive.
credentials_drive = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES_DRIVE)
drive_service = build('drive', 'v3', credentials=credentials_drive)

# === FUNCTION TO LIST ALL PDF FILES IN A GOOGLE DRIVE FOLDER ===
def list_pdf_files_in_folder(folder_id):
    """
    Lists all PDF files in a specific Google Drive folder.
    :param folder_id: ID of the Google Drive folder.
    :return: List of file IDs and names for all PDF files in the folder.
    """
    try:
        # Query to find all PDF files in the specified folder.
        query = f"'{folder_id}' in parents and mimeType='application/pdf'"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if not files:
            print("No PDF files found in the folder.")
            return []

        # Print the list of PDF files found.
        print("PDF files found in the folder:")
        for file in files:
            print(f"File Name: {file['name']}, File ID: {file['id']}")

        return files
    except Exception as e:
        print(f"Error listing PDF files: {e}")
        return []

# === FUNCTION TO DOWNLOAD A FILE FROM GOOGLE DRIVE ===
def download_file(file_id, file_name, destination_folder):
    """
    Downloads a file from Google Drive using its file ID and saves it to the specified local folder.
    :param file_id: ID of the file to download.
    :param file_name: Name of the file to save.
    :param destination_folder: Local folder where the file will be saved.
    """
    try:
        # Define the full path for the downloaded file.
        destination_path = os.path.join(destination_folder, file_name)

        # Request the file content from Google Drive.
        request = drive_service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as fh:
            # Download the file in chunks and save it to the local path.
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Downloading {file_name}: {int(status.progress() * 100)}% done.")

        print(f"File downloaded successfully: {destination_path}")
    except Exception as e:
        print(f"Error downloading file {file_name}: {e}")

# === MAIN LOGIC TO DOWNLOAD ALL PDF FILES FROM A FOLDER ===
# ID of the Google Drive folder containing the PDF files.
folder_id = '1ngPkxMzO0SEdsqNn2yRuj_kxLjAazRmk'  # Replace with the actual folder ID. THE GOOGLE DRIVERS FOLDER HAS TO BE SHARED WITH THE 
# GOOGLE CLOUD SERVICE CLIENT E-MAIL
# THIS IS THE INPUT FOR THE SOFTWARE (USERS INPUT FOR A EVENTUAL GUI)

# Local directory where the downloaded PDF files will be saved.
pdf_directory = "C:/Users/Gustavo Cunha/Downloads/Automation_PDFs"  # Replace with your desired local folder path.
# THIS IS THE INPUT FOR THE SOFTWARE (USERS INPUT FOR A EVENTUAL GUI)

# Create the destination folder if it doesn't exist.
if not os.path.exists(pdf_directory):
    os.makedirs(pdf_directory)

# List all PDF files in the Google Drive folder.
pdf_files = list_pdf_files_in_folder(folder_id)

# Download each PDF file to the local folder.
for pdf_file in pdf_files:
    file_id = pdf_file['id']
    file_name = pdf_file['name']
    download_file(file_id, file_name, pdf_directory)


# SECTION 2: READING PDF FILES DOWNLOADED AND CALCULATING GLOBAL BALANCE

import pdfplumber
import re

# Function to extract the statement balance and period from a single PDF file.
def extract_balance_and_period(pdf_path):
    """
    Extracts the statement period and balance from a PDF file.
    :param pdf_path: Path to the PDF file.
    :return: Start date, end date, and balance of the statement. Returns None if the data cannot be extracted.
    """
    with pdfplumber.open(pdf_path) as pdf:
        # Extract text from all pages of the PDF and concatenate it into a single string.
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    # Regular expression to find the statement period in the format "Month Day, Year to Month Day, Year".
    period_pattern = r"for (\w+ \d{1,2}, \d{4}) to (\w+ \d{1,2}, \d{4})"
    match = re.search(period_pattern, text)

    if not match:
        print(f"[ERROR] Could not find period. {pdf_path}.")
        return None, None, None

    # Extract the start and end dates of the statement period.
    start_date, end_date = match.groups()
    print(f"Period found on file {pdf_path}: {start_date} to {end_date}")

    # Regular expression to find all occurrences of "balance on" followed by a date and an amount.
    balance_pattern = r"balance on (\w+ \d{1,2}, \d{4}) (\$[\d,]+\.\d{2})"
    matches = re.findall(balance_pattern, text)

    if not matches:
        print(f"[ERROR] No occurrences of 'balance on' found on file {pdf_path}.")
        return start_date, end_date, None

    # Filter the correct occurrence of "balance on" where the date matches the end date of the statement period.
    correct_balance = None
    for date, amount in matches:
        if date == end_date:
            # Convert the balance amount to a float (remove '$' and ',').
            correct_balance = float(amount.replace("$", "").replace(",", ""))
            break

    if correct_balance is None:
        print(f"[ERROR] No 'balance on' date matches the final date of the statement period on file {pdf_path}.")
    
    return start_date, end_date, correct_balance

# List all PDF files in the local directory.
pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]

# Variables to store the total balance and the global start and end dates.
total_balance = 0.0
global_start_date = None
global_end_date = None

# Process each PDF file to accumulate the total balance and determine the global period.
for pdf_file in sorted(pdf_files):  # Sort files alphabetically to maintain chronological order.
    pdf_path = os.path.join(pdf_directory, pdf_file)
    start_date, end_date, balance = extract_balance_and_period(pdf_path)

    if balance is not None:
        # Accumulate the balance and update the global start and end dates.
        total_balance += balance
        if global_start_date is None or start_date < global_start_date:
            global_start_date = start_date
        if global_end_date is None or end_date > global_end_date:
            global_end_date = end_date


# SECTION 3: CREATE A NEW SPREADSHEET AND WRITE RESULTS

# Create a new spreadsheet and write the results.
def create_spreadsheet_and_write_results(folder_id, global_start_date, global_end_date, total_balance):
    """
    Creates a new spreadsheet in the specified Google Drive folder and writes the results.
    :param folder_id: ID of the Google Drive folder where the spreadsheet will be created.
    :param global_start_date: Start date of the entire period analyzed.
    :param global_end_date: End date of the entire period analyzed.
    :param total_balance: Global final balance calculated.
    """
    try:
        # Create a new spreadsheet.
        spreadsheet_metadata = {
            'name': 'Global_Balance_Report',
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': [folder_id]
        }
        spreadsheet = drive_service.files().create(body=spreadsheet_metadata, fields='id').execute()
        spreadsheet_id = spreadsheet['id']
        print(f"New spreadsheet created. Spreadsheet ID: {spreadsheet_id}")

        # Write the results to the spreadsheet.
        sheet_service = build('sheets', 'v4', credentials=credentials_drive)
        body = {
            'values': [
                ["Entire Period Analyzed", f"{global_start_date} to {global_end_date}"],
                ["Global Final Balance", f"${total_balance:,.2f}"]
            ]
        }
        sheet_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="A1",  # Write to the top-left corner of the sheet.
            valueInputOption="RAW",
            body=body
        ).execute()
        print("Results written to the spreadsheet.")
    except Exception as e:
        print(f"Error creating or writing to spreadsheet: {e}")

# Create the spreadsheet and write the results.
create_spreadsheet_and_write_results(folder_id, global_start_date, global_end_date, total_balance)