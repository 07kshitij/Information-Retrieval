from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
import os
import re
import string
import json

DEBUG = True
DATA_PATH = './ECTText/'

inverted_index = dict()

lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')

''' Sorting function to sort input files in lexicographically increasing order '''


def sortKey(s):
    return int(s.split('.')[0])


files = os.listdir(DATA_PATH)
files.sort(key=sortKey)

''' Extract the tokens after stopwords | punctuation removal followed by lemmatization
    and build the inverted_index '''


def build_inverted_index():

    file_num = 0
    for file in files:
        with open(os.path.join(DATA_PATH, file), 'r', encoding='utf-8') as ECTText:
            text = ECTText.read().replace('\n', ' ').lower().strip()
            for token in word_tokenize(text):
                # Remove stop words & punctuation marks
                if token not in stopwords and token not in string.punctuation:
                    lemma = lemmatizer.lemmatize(token)
                    if lemma not in inverted_index.keys():
                        inverted_index[lemma] = []
            position = 0
            for word in text.split():
                word.replace(',', '')
                word.replace('.', '')
                word = word.strip()
                if word in inverted_index.keys():
                    inverted_index[word].append((file_num, position))
                position = position + 1
            file_num += 1
            if DEBUG and file_num % 100 == 0:
                print("Tokenization - Steps done: {} | Tokens found: {}".format(
                    file_num, len(inverted_index.keys())))

    if DEBUG:
        print("Total number of tokens: {}".format(len(inverted_index.keys())))
    with open('inverted_index.json', 'w') as inv_idx:
        json.dump(inverted_index, inv_idx)


if __name__ == "__main__":
    build_inverted_index()
