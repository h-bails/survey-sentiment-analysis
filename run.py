import gspread
from google.oauth2.service_account import Credentials
from tabulate import tabulate
from collections import Counter
import spacy
from spacy.matcher import Matcher
from spacytextblob.spacytextblob import SpacyTextBlob
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pathlib

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

print("Welcome to the Survey Sentiment Analyser!\n")
print("This program can help you perform sentiment analysis on\nopen-text responses on a Google Sheet.")
input("Press Enter to begin the data analysis.\n")

print("Fetching available data categories...\n")


def fetch_headers():
    """
    Displays the data available for analysis by arranging headers into a dict, 
    then tabulating the dict using tabulate
    """
    data = SHEET.worksheet('data').get_all_values()
    header_title = data[0]
    header_num = list(range(1, (len(header_title)+1)))
    header_dict = {}
    for title, num in zip(header_title, header_num):
        header_dict[title] = num
    print(tabulate(header_dict.items(), headers = ["Question", "Option"]))
    print("\nTo begin analysing answers to a question,\nenter its allocated number followed by Enter.\n")

    while True:
        try:
            header_choice = input("Enter your choice here: ")
            if header_choice in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]:
                break
            else:
                raise ValueError("Number not in list")
        except ValueError as e:
            print(f"{e}: Invalid selection. Please try again.")
            continue
            
    print("Great! Let's analyse your data!")          
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
    doc = nlp(string, disable = ['ner'])
    words = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    word_freq = Counter(words).most_common(10)
    
    lemmatized_string = ' '.join(words)
    phrase_doc = nlp(lemmatized_string, disable = ['ner'])
    matcher = Matcher(nlp.vocab) 
    pattern = [{'POS':'ADJ'}, {'POS':'NOUN'}] 
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
    print("\nSentiment of responses:\n")
    print(sentiment_score)

    if round(sentiment_score) == -1:
        print("\nSentiment of responses skewed towards *Negative*.")
    elif round(sentiment_score) == 1:
        print("\nSentiment of responses skewed towards *Positive*.")
    elif round(sentiment_score) == 0:
        print("\nSentiment of responses was largely *Neutral*.")



def build_word_cloud(string):
    doc = nlp(string, disable = ['ner'])
    words = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]

    lemmatized_string = ' '.join(words)
    phrase_doc = nlp(lemmatized_string, disable = ['ner'])
    matcher = Matcher(nlp.vocab) 
    pattern = [{'POS':'ADJ'}, {'POS':'NOUN'}] 
    matcher.add('ADJ_PHRASE', [pattern]) 
    phrase_matches = matcher(phrase_doc, as_spans=True) 
    phrases = [] 
    for span in phrase_matches:
        phrases.append(span.text.lower())
    phrases_string = ' '.join(phrases)
    wordcloud = WordCloud().generate(phrases_string)
    plt.imshow(wordcloud)
    wordcloud.to_file("./wordcloud.png")
    print("Your WordCloud is now available.")
    print("Please refresh the page to view it. (You can Right click > Save as... on the image to download.).")

 

header_choice = fetch_headers()
data_string = get_selected_data(header_choice)
analyse_themes(data_string)
build_word_cloud(data_string)
