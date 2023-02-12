from collections import Counter
import pathlib
import random
import sys
import gspread
from google.oauth2.service_account import Credentials
from tabulate import tabulate
import spacy
from spacy.matcher import Matcher
from spacytextblob.spacytextblob import SpacyTextBlob
import matplotlib.pyplot as plt
from wordcloud import WordCloud

nlp = spacy.load('en_core_web_sm')
nlp.add_pipe('spacytextblob')
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


def fetch_headers():
    """
    Displays the data available for analysis by arranging headers into a dict,
    then tabulating the dict using the tabulate module.
    """
    data = SHEET.worksheet('data').get_all_values()
    header_title = data[0]
    header_num = list(range(1, (len(header_title)+1)))
    header_dict = {}
    for title, num in zip(header_title, header_num):
        header_dict[title] = num
    print(tabulate(header_dict.items(), headers=["Question", "Option"]))
    print("\nTo begin analysing survey data,")
    print("enter its allocated number followed by \'Enter\'.\n")

    while True:
        try:
            header_choice = input("Enter your choice here: ")
            if int(header_choice) in header_num:
                break
            elif header_choice == "0":
                raise ValueError("Invalid selection")
            elif header_choice == "exit":
                sys.exit(0)
            else:
                raise ValueError("Invalid selection")
        except ValueError as error:
            print(f"{error}: Number not in list. Please try again.")
            continue

    print("Great! Let's analyse your data!\n")
    return header_choice


def get_selected_data(selection):
    """
    Fetches the data from the specified column and
    concatenates it into a single string for analysis.
    Prepares the string for sentiment analysis.
    """
    worksheet = SHEET.worksheet('data')
    data_to_analyse = worksheet.col_values(selection)
    data_string = ' '.join(data_to_analyse)

    return data_string


def analyse_themes(string):
    """
    Tokenises and lemmatizes the words in the string,
    assigning them lemma values.
    Ignores stop words and punctuation.
    Analyses the string for frequency of words and phrases.
    Assigns a sentiment score to the answers to the question.
    """
    doc = nlp(string, disable=['ner'])
    words = [token.lemma_ for token in doc if not
             token.is_stop and not token.is_punct]
    word_freq = Counter(words).most_common(10)

    lemmatized_string = ' '.join(words)
    phrase_doc = nlp(lemmatized_string, disable=['ner'])
    matcher = Matcher(nlp.vocab)
    pattern = [{'POS': 'ADJ'}, {'POS': 'NOUN'}]
    matcher.add('ADJ_PHRASE', [pattern])
    phrase_matches = matcher(phrase_doc, as_spans=True)
    phrases = []
    for span in phrase_matches:
        phrases.append(span.text.lower())
    phrase_freq = Counter(phrases).most_common(10)

    print("\nMost common phrases:")
    print(tabulate(phrase_freq))

    print("\nMost common words:")
    print(tabulate(word_freq))

    sentiment_polarity = doc._.blob.polarity
    sentiment_score = round(sentiment_polarity, 1)
    print("\nSentiment score of responses:\n")
    print(sentiment_score)

    if sentiment_score <= 1 and sentiment_score >= 0.6:
        print("\nSentiment of responses was *Very Positive*.\n")
    elif sentiment_score < 0.6 and sentiment_score > 0.1:
        print("\nSentiment of responses was *Positive*.\n")   
    elif sentiment_score <= 0.1 and sentiment_score >= -0.1:
        print("\nSentiment of responses was *Neutral*.\n")
    elif sentiment_score > -0.6 and sentiment_score < -0.1:
        print("\nSentiment of responses was *Negative*.\n")                
    elif sentiment_score >= -1 and sentiment_score <= 0.6:
        print("\nSentiment of responses was *Very Negative*.\n")

    print("What do you want to do next?\n")

    while True:
        try:
            word_cloud_choice = input("1: Add this data to my Google Sheet\
                \n2: Build a Word Cloud using this data\
                \n3: Analyze another data category\n\
                \nYour choice: ")
            if word_cloud_choice == "1":
                append_data(word_freq, phrase_freq, sentiment_score)
                break
            elif word_cloud_choice == "2":
                print("OK! Building your Word Cloud...\n")
                build_word_cloud(phrases)
                break
            elif word_cloud_choice == "3":
                print("OK! Taking you back to the home screen...\n")
                main()
                break
            elif word_cloud_choice == "exit":
                sys.exit(0)
            else:
                raise ValueError("Invalid selection")
        except ValueError as error:
            print(f"{error}: Available options are 1 or 2. Please try again.")
            continue


def append_data(words, phrases, sentiment):
    """
    Creates a new worksheet with a random name.
    Appends most common words, phrases and sentiment score
    to the new worksheet.
    """
    print('\nUpdating worksheet...\n')
    random_num = random.choice(range(1000, 9999))
    worksheet_title = '_'.join(["worksheet", str(random_num)])
    worksheet = SHEET.add_worksheet(title=worksheet_title, rows=100, cols=20)
    
    words_list = [list(row) for row in words]
    phrases_list = [list(row) for row in phrases]
    
    worksheet.append_row(["Most common words:"], table_range='A1:B1')
    worksheet.append_rows(words_list, table_range='A1:B1')

    worksheet.append_row(["Most common phrases:"], table_range='A13:B13')
    worksheet.append_rows(phrases_list)

    worksheet.append_row(["Overall sentiment score:"], table_range='A25:B25')
    worksheet.append_row([sentiment], table_range='A26:B26')
    print('\nWorksheet updated.\n')

    print("What do you want to do next?\n")

    while True:
        try:
            step_choice = input("1: Build a Word Cloud using this data\
                \n2: Analyze another data category\n\
                \nexit: Exit the program\
                \nYour choice: ")
            if step_choice == "1":
                print("OK! Building your Word Cloud...\n")
                build_word_cloud(phrases)
                break
            elif step_choice == "2":
                print("OK! Taking you back to the home screen...\n")
                main()
                break
            elif step_choice == "exit":
                sys.exit(0)
            else:
                raise ValueError("Invalid selection")
        except ValueError as error:
            print(f"{error}: Available options are 1, 2, or \'exit\'.\
                \nPlease try again.")
            continue
    

def build_word_cloud(string):
    """
    Builds a word cloud out of most common phrases in
    selected data category
    """
    phrases_string = ' '.join(string)
    wordcloud = WordCloud().generate(phrases_string)
    plt.imshow(wordcloud)
    wordcloud.to_file("./wordcloud.png")

    print("\nYour WordCloud is now available.\n")
    print("Please refresh the page to view and download it.\n")

    file_name = "wordcloud.png"
    base_url = pathlib.Path(__file__).resolve().parent.parent
    file_path = base_url / 'media' / file_name
    wordcloud_sheet = SHEET.worksheet('WordCloud')
    wordcloud_sheet.update_cell(1, 1, f'=IMAGE("{file_path}")')


def main():
    """
    Run all program functions
    """
    header_choice = fetch_headers()
    data_string = get_selected_data(header_choice)
    analyse_themes(data_string)


print("Welcome to the Survey Sentiment Analyser!\n")
print("This program can help you perform sentiment analysis on")
print("open-text survey responses in a Google Sheet.\n")
print("Type \'exit\' at any time to terminate the program.\n")

input("Press \'Enter\' to begin the data analysis.\n")

print("Fetching available data categories...\n")
main()
