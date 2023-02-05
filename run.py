import gspread
from google.oauth2.service_account import Credentials
from tabulate import tabulate

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

CREDS = Credentials.from_service_account_file("creds.json")
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open("sentiment-analysis-data-set")

data = SHEET.worksheet('data').get_all_values()



print(f"Welcome to the Survey Sentiment Analyser!\n")
print(f"This program can help you perform sentiment analysis on \n open-text responses on a Google Sheet.")
print(f"Press any key to begin the data analysis.\n")

print(f"Fetching available data categories...\n")

def fetch_headers():
    """
    Displays the data available for analysis by arranging headers into a list
    """
    header_title = data[0]
    header_num = list(range(len(header_title)))
    header_dict = {}
    for title, num in zip(header_title, header_num):
        header_dict[title] = num
    print(tabulate(header_dict.items(), headers = ["Topic", "Number"]))
    print(f"\n To begin analysing a topic, enter the number of the topic followed by Enter.")


fetch_headers()