"""
Survey Sentiment Analyser imports
"""
# import in-built Python modules
from collections import Counter
import random
import sys
# import Google credentials, and Drive + Sheets api
import gspread
from google.oauth2.service_account import Credentials
# import visual presentation aids
from tabulate import tabulate
import colorama
from colorama import Fore
# import spacy for sentiment analysis
import spacy
from spacy.matcher import Matcher
from spacytextblob.spacytextblob import SpacyTextBlob  # noqa # pylint: disable=unused-import
# import matplotlib and wordcloud to build word clouds
import matplotlib.pyplot as plt
from wordcloud import WordCloud


SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# global variables
CREDS = Credentials.from_service_account_file("creds.json")
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open("sentiment-analysis-data-set")
nlp = spacy.load('en_core_web_sm')
nlp.add_pipe('spacytextblob')


def fetch_headers():
    """
    Displays the data available for analysis by arranging sheet
    headers into a dict, then tabulating the dict.
    Prompts the user to choose which data category they want to analyse.
    Validates the user's input.
    """
    data = SHEET.worksheet('data').get_all_values()
    header_title = data[0]
    header_num = list(range(1, (len(header_title)+1)))
    header_num_string = [str(num) for num in header_num]
    header_dict = {}
    for title, num in zip(header_title, header_num):
        header_dict[title] = num
    print(tabulate(header_dict.items(), headers=["Question", "Option"]))
    print("\nTo begin analysing survey data,")
    print("enter its allocated number followed by \'Enter\'.\n")

    while True:
        try:
            header_choice = input("Enter your choice here:\n")
            if header_choice in header_num_string:
                break
            elif header_choice == "0":
                raise ValueError("Invalid selection")
            elif header_choice == "exit":
                sys.exit(0)
            else:
                raise ValueError("Invalid selection")
        except ValueError as error:
            print(Fore.RED + f"{error}: Number not in list. Please try again.")
            continue

    print(Fore.GREEN + "Great! Let's analyse your data!\n")
    return header_choice


def get_selected_data(selection):
    """
    Fetches the data from the specified column.
    Prepares the data for analysis by concatenating
    it into a single string.
    Returns the concatenated data string.
    """
    worksheet = SHEET.worksheet('data')
    data_to_analyse = worksheet.col_values(selection)
    data_string = ' '.join(data_to_analyse)

    return data_string


def analyse_themes(string):
    """
    Tokenises and lemmatizes the words in the string (i.e. assigns each
    word the relevant part of speech & reduces them to their base forms).
    Ignores stop words and punctuation.
    Analyses the string for frequency of words and phrases.
    Assigns a sentiment score to the answers to the question.
    Gives the user the option of what to do next, and validates their input.
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
        print("\nSentiment of responses was" + Fore.GREEN +
              "*Very Positive*.\n")
    elif sentiment_score < 0.6 and sentiment_score > 0.1:
        print("\nSentiment of responses was" + Fore.GREEN + " *Positive*.\n")
    elif sentiment_score <= 0.1 and sentiment_score >= -0.1:
        print("\nSentiment of responses was" + Fore.YELLOW + " *Neutral*.\n")
    elif sentiment_score > -0.6 and sentiment_score < -0.1:
        print("\nSentiment of responses was" + Fore.RED + " *Negative*.\n")
    elif sentiment_score >= -1 and sentiment_score <= 0.6:
        print("\nSentiment of responses was" + Fore.RED +
              " *Very Negative*.\n")

    print(Fore.CYAN + "What do you want to do next?\n")

    while True:
        try:
            word_cloud_choice = input("1: Add this data to my Google Sheet\
                \n2: Build a Word Cloud using this data\
                \n3: Analyse another data category\n\
                \nYour choice:\n")
            if word_cloud_choice == "1":
                append_data(word_freq, phrase_freq, sentiment_score, phrases)
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
            print(Fore.RED + f"{error}: Available options are 1 or 2, 3,"
                  + " or \'exit\'. Please try again.")
            continue


def append_data(freq1, freq2, sent, phrases):
    """
    Creates a new worksheet with a random name.
    Appends the most common words, phrases and sentiment score
    to the new worksheet.
    Gives the user the option of what to do next, and validates their input.
    """
    print('\nUpdating worksheet...\n')
    random_num = random.choice(range(1000, 9999))
    worksheet_title = '_'.join(["worksheet", str(random_num)])
    worksheet = SHEET.add_worksheet(title=worksheet_title, rows=100, cols=20)

    words_list = [list(row) for row in freq1]
    phrases_list = [list(row) for row in freq2]

    worksheet.append_row(["Most common words:"], table_range='A1:B1')
    worksheet.append_rows(words_list, table_range='A1:B1')

    worksheet.append_row(["Most common phrases:"], table_range='A13:B13')
    worksheet.append_rows(phrases_list)

    worksheet.append_row(["Overall sentiment score:"], table_range='A25:B25')
    worksheet.append_row([sent], table_range='A26:B26')
    print(Fore.GREEN + '\nWorksheet updated.\n')

    print(Fore.CYAN + "What do you want to do next?\n")

    while True:
        try:
            step_choice = input("1: Download a Word Cloud from this data\
                \n2: Analyse another data category\
                \nexit: Exit the program\n\
                \nYour choice:\n")
            if step_choice == "1":
                print("OK! Fetching your Word Cloud...\n")
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
            print(Fore.RED + f"{error}: Available options are 1, 2, or"
                  + " \'exit\'. Please try again.")
            continue


def build_word_cloud(string):
    """
    Builds a word cloud out of the most common phrases in the
    selected data category.
    Saves wordcloud to the /static/ folder with a random name.
    Also displays a static image of the wordcloud due to Heroku constraints.
    Gives the user the option of what to do next, and validates their input.
    """
    phrases_string = ' '.join(string)
    wordcloud = WordCloud(background_color="white",
                          width=800, height=400).generate(phrases_string)
    plt.imshow(wordcloud)
    random_num = random.choice(range(1000, 9999))
    wordcloud_name = '_'.join(["wordcloud", str(random_num)])
    wordcloud_path = f"static/{wordcloud_name}.png"
    wordcloud.to_file(wordcloud_path)

    short_path = 'https://res.cloudinary.com/hwvf6ormz/image/upload/'

    if header_choice == "1":
        wordcloud_url = short_path + "v1676571064/wordcloud_7289_y9dtvm.png"
    elif header_choice == "2":
        wordcloud_url = short_path + "v1676571249/wordcloud_7156_hukmw2.png"
    elif header_choice == "3":
        wordcloud_url = short_path + "v1676571304/wordcloud_4527_pux62s.png"
    elif header_choice == "4":
        wordcloud_url = short_path + "v1676571438/wordcloud_4473_f9nfuw.png"
    elif header_choice == "5":
        wordcloud_url = short_path + "v1676571487/wordcloud_6742_b0jpg4.png"

    print(Fore.GREEN + "\nWordcloud saved to the home directory.\n")
    print(f"\nYou can also view it here: {wordcloud_url}\n")

    print(Fore.CYAN + "What do you want to do next?\n")

    while True:
        try:
            step_choice = input("1: Analyse another data category\
                \nexit: Exit the program\n\
                \nYour choice:\n")
            if step_choice == "1":
                print("OK! Taking you back to the home screen...\n")
                main()
                break
            elif step_choice == "exit":
                sys.exit(0)
            else:
                raise ValueError("Invalid selection")
        except ValueError as error:
            print(Fore.RED + f"{error}: Available options are 1, or \'exit\'."
                  + " Please try again.")
            continue


def main():
    """
    Run all program functions
    """
    colorama.init(autoreset=True)
    start()
    global header_choice
    header_choice = fetch_headers()
    data_string = get_selected_data(header_choice)
    analyse_themes(data_string)


def start():
    """
    Prints the introduction to the program
    """
    print(Fore.MAGENTA + "Welcome to the Survey Sentiment Analyser!\n")
    print("This program can help you perform sentiment analysis on")
    print("open-text survey responses in a Google Sheet.\n")
    print("Type \'exit\' at any time to terminate the program.\n")

    input(Fore.CYAN + "Press \'Enter\' to begin the data analysis.\n")

    print("Fetching available data categories...\n")


if __name__ == "__main__":
    main()
