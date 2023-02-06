import gspread
from google.oauth2.service_account import Credentials
from tabulate import tabulate
from collections import Counter
import spacy
from spacy.matcher import Matcher
nlp = spacy.load('en_core_web_sm')
nlp.max_length = 185000


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
    header_num = list(range(1, (len(header_title) +1)))
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

def get_selected_data(selection):
    """
    Fetches the data from the specified column and concatenates it into a single string for analysis.
    Prepares the string for sentiment analysis.
    """
    worksheet = SHEET.worksheet('data')
    data_to_analyse = worksheet.col_values(selection)
    data_string = ' '.join(data_to_analyse)
    
    return data_string

def analyse_themes(string):
    """
    Tokenises the words in the string, assigning them lemma values.
    Ignores stop words and punctuation.
    Analyses the string for frequency of phrases.
    """
    doc = nlp(data_string, disable = ['ner'])
    words = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    word_frequency = Counter(words).most_common(10)
    
    matcher = Matcher(nlp.vocab) 
    pattern = [{'POS':'ADJ'}, {'POS':'NOUN'}] 
    matcher.add('ADJ_PHRASE', [pattern]) 
    matches = matcher(doc, as_spans=True) 
    phrases = [] 
    for span in matches:
        phrases.append(span.text.lower())
        phrase_freq = Counter(phrases)
    
    print("Most common phrases")
    print(tabulate(phrase_freq.most_common(10)))

    print("Most common words:")
    print(tabulate(word_frequency))

    

    

header_choice = fetch_headers()
data_string = get_selected_data(header_choice)
analyse_themes(data_string)

