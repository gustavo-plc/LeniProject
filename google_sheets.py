# SECTION 1: CONNECTING TO SPREADSHEET AND DOWNLOADING GOOGLE DRIVE FILE TO LOCAL PC 

import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials

# === SETTING UP ===
# Path to the service account JSON file used for authentication with Google APIs.
SERVICE_ACCOUNT_FILE = 'C:/Users/Gustavo Cunha/Downloads/wired-height-451613-b4-40d0526c8cdc.json'

# Scopes define the level of access the application has to Google Sheets and Google Drive.
SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive.readonly']

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

# Name of the file to search for and download from Google Drive.
file_name = 'test.pdf'

# === FUNCTION TO SEARCH AND GET THE FILE FROM GOOGLE DRIVE ===
def get_file(file_name):
    """
    Searches for a file in Google Drive by its name and returns its ID.
    :param file_name: Name of the file to search for.
    :return: File ID if found, otherwise None.
    """
    query = f"name = '{file_name}'"
    try:
        # Execute the search query to find files with the specified name.
        results = drive_service.files().list(q=query).execute()
        items = results.get('files', [])
        
        if not items:
            print('File not found.')
            return None

        # Debug: List all files found with the specified name.
        # This helps verify that the correct file is being retrieved.
        for item in items:
            print(f"Files found: {item['name']} (ID: {item['id']})")
        
        # Return the ID of the first file found (assuming there is only one file with the specified name).
        return items[0]['id']
    except Exception as e:
        print(f"Error on searching file: {e}")
        return None

# === FUNCTION TO DOWNLOAD FILE FROM GOOGLE DRIVE ===
def download_file(file_id, destination_path):
    """
    Downloads a file from Google Drive using its file ID and saves it to the specified local path.
    :param file_id: ID of the file to download.
    :param destination_path: Local path where the file will be saved.
    """
    try:
        # Request the file content from Google Drive.
        request = drive_service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as fh:
            # Download the file in chunks and save it to the local path.
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% done.")

        print(f"File downloaded successfully: {destination_path}")
    except Exception as e:
        print(f"Error on downloading file: {e}")

# === GETTING ID AND DOWNLOADING THE FILE ===
# Define the local path where the downloaded file will be saved.
file_destination = "C:/Users/Gustavo Cunha/Downloads/teste_baixado.pdf"
# Get the file ID from Google Drive.
file_id = get_file(file_name)
if file_id:
    # Download the file using its ID and save it to the specified destination.
    download_file(file_id, file_destination)


# SECTION 2: READING PDF FILES DOWNLOADED AND CALCULATING GLOBAL BALANCE

import pdfplumber
import re
import os

# Local directory where downloaded PDF files are stored.
pdf_directory = "C:/Users/Gustavo Cunha/Downloads/"

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

# Display the final global balance and period after processing all PDF files.
if global_start_date and global_end_date:
    print("\n================= FINAL REPORT =================")
    print(f"Entire period analyzed: {global_start_date} to {global_end_date}")
    print(f"Global final balance: ${total_balance:,.2f}")
    print("===================================================")
else:
    print("\n[ERROR] The global final balance could not be calculated.")