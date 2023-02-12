from collections import Counter
import pathlib
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
    print("enter its allocated number followed by Enter.\n")

    while True:
        try:
            header_choice = input("Enter your choice here: ")
            if header_choice in ["1", "2", "3", "4", "5"]:
                break
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

    sentiment_score = doc._.blob.polarity
    print("\nSentiment score of responses:\n")
    print(round(sentiment_score, 3))

    if round(sentiment_score) == -1:
        print("\nSentiment of responses skewed towards *Negative*.\n")
    elif round(sentiment_score) == 1:
        print("\nSentiment of responses skewed towards *Positive*.\n")
    elif round(sentiment_score) == 0:
        print("\nSentiment of responses was largely *Neutral*.\n")

    print("What do you want to do next?\n")

    while True:
        try:
            word_cloud_choice = input("Enter 1 to build a word cloud of this\
                \ndata, or 2 to analyze more data: ")
            if word_cloud_choice == "1":
                print("OK! Building your Word Cloud...\n")
                build_word_cloud(phrases)
                break
            elif word_cloud_choice == "2":
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
input("Press Enter to begin the data analysis.\n")

print("Fetching available data categories...\n")
main()
