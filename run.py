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



print(f"Welcome to the Survey Sentiment Analyser!\n")
print(f"This program can help you perform sentiment analysis on\nopen-text responses on a Google Sheet.")
input(f"Press Enter to begin the data analysis.\n")

print(f"Fetching available data categories...\n")

def fetch_headers():
    """
    Displays the data available for analysis by arranging headers into a dict, 
    then tabulating the dict using tabulate
    """
    data = SHEET.worksheet('data').get_all_values()
    header_title = data[0]
    header_num = list(range(len(header_title)))
    header_dict = {}
    for title, num in zip(header_title, header_num):
        header_dict[title] = num
    print(tabulate(header_dict.items(), headers = ["Topic", "Number"]))
    print(f"\nTo begin analysing a topic, enter the number of the topic followed by Enter.\n")
    header_choice = input("Enter your data here: ")
    
    try:
        if header_choice in header_dict.values():
            print(f"You chose topic {header_choice}!")
    except ValueError:
        print(f"Invalid header choice provided: {header_choice}. Please select a number from the list above\nand press Enter.")
        return False

    return header_choice


fetch_headers()
