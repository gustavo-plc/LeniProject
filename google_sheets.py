# SECTION 1: CONNECTING TO SPREADSHEET AND DOWNLOADING GOOGLE DRIVE FILE TO LOCAL PC 

import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials

# === SETTING UP ===
SERVICE_ACCOUNT_FILE = 'C:/Users/Gustavo Cunha/Downloads/wired-height-451613-b4-40d0526c8cdc.json'  # SERVICE ACCOUNT JASON FILE PATH

SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive.readonly']

# === CONNECTION AND AUTHENTICATION WITH GOOGLE SHEETS ===
credentials_sheets = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES_SHEETS)
client = gspread.authorize(credentials_sheets)

# OPEN SPREADSHEET THROUGH ID (DIDN'T WORK WITH URL)
spreadsheet = client.open_by_key('1rzekD9oi277hQf2kQqXfbP8kVB8pUB8X3qjy_IRGYkI')
worksheet = spreadsheet.worksheet('Copy of 110-3b_AB_2024_OCCU_9357_PERS_CCRD') #SPREADSHEET TAB

print("SUCESSFULLY CONNECTED TO SPREADSHEET!")

# === CONNECTION AND AUTHENTICATION WITH GOOGLE DRIVE ===
credentials_drive = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES_DRIVE)
drive_service = build('drive', 'v3', credentials=credentials_drive)

# FILE NAME AT GOOGLE DRIVE
file_name = 'test.pdf'

# === FUNCTION TO SEARCH AND GET THE FILE FROM GOOGLE DRIVE ===
def get_file(file_name):
    query = f"name = '{file_name}'"
    try:
        results = drive_service.files().list(q=query).execute()
        items = results.get('files', [])
        
        if not items:
            print('File not found.')
            return None

        # Debug: Listing files found
        for item in items:
            print(f"Files found: {item['name']} (ID: {item['id']})")
        
        return items[0]['id']  # RETURNS THE ID OF THE FIRST FILE FOUND
    except Exception as e:
        print(f"Error on searching file: {e}")
        return None

# === FUNCTION TO DOWNLOAD FILE FROM GOOGLE DRIVE ===
def download_file(file_id, destination_path):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% done.")

        print(f"File downloaded sucessfully: {destination_path}")
    except Exception as e:
        print(f"Erro on downloading file: {e}")

# === GETTING ID AND DOWNLOADING THE FILE ===

file_destination = "C:/Users/Gustavo Cunha/Downloads/teste_baixado.pdf"
file_id = get_file(file_name)
if file_id:
    download_file(file_id, file_destination)


# SECTION 2: READING PDF FILES DOWNLOADED AND CALCULATING GLOBAL BALANCE

import pdfplumber
import re
import os

# Local Directory where downloaded PDF files are stored
pdf_directory = "C:/Users/Gustavo Cunha/Downloads/"

# Function to get statement balance and period from only one pdf
def extract_balance_and_period(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    # Expression definition to find the statement period
    period_pattern = r"for (\w+ \d{1,2}, \d{4}) to (\w+ \d{1,2}, \d{4})"
    match = re.search(period_pattern, text)

    if not match:
        print(f"[ERROR] Could not find period. {pdf_path}.")
        return None, None, None

    start_date, end_date = match.groups()
    print(f"Period found on file {pdf_path}: {start_date} to {end_date}")

    # Regular expression to find all occurrences of "balance on"
    balance_pattern = r"balance on (\w+ \d{1,2}, \d{4}) (\$[\d,]+\.\d{2})"
    matches = re.findall(balance_pattern, text)

    if not matches:
        print(f"[ERROR] None occurrences of 'balance on' found on file {pdf_path}.")
        return start_date, end_date, None

    # Filter the correct occurrence of "balance on" in the pdf, which the date after "balance on" is equal to 'end_date'
    correct_balance = None
    for date, amount in matches:
        if date == end_date:
            correct_balance = float(amount.replace("$", "").replace(",", ""))
            break

    if correct_balance is None:
        print(f"[ERROR] None 'balance on' date matches the final date of statement period on file {pdf_path}.")
    
    return start_date, end_date, correct_balance

# Lists all PDF files on the local directory
pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]

# Variables declaration to store the total balance info
total_balance = 0.0
global_start_date = None
global_end_date = None

# Processing of each pdf to accumulate values
for pdf_file in sorted(pdf_files):  # alphabetically sorted to mantain cronological order
    pdf_path = os.path.join(pdf_directory, pdf_file)
    start_date, end_date, balance = extract_balance_and_period(pdf_path)

    if balance is not None:
        total_balance += balance
        if global_start_date is None or start_date < global_start_date:
            global_start_date = start_date
        if global_end_date is None or end_date > global_end_date:
            global_end_date = end_date

#  Show the final global balance, after processing all pdf local files. 
if global_start_date and global_end_date:
    print("\n================= FINAL REPORT =================")
    print(f"Entire period analised: {global_start_date} to {global_end_date}")
    print(f"Global final balance: ${total_balance:,.2f}")
    print("===================================================")
else:
    print("\n[ERROR] The global final balance could not be calculated.")
