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

tokens = set()
lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')
inverted_index = dict()
files = os.listdir(DATA_PATH)
files.sort()


def get_tokens():
    cnt = 0

    token_file = open('tokens.txt', 'w')

    for file in files:
        with open(os.path.join(DATA_PATH, file), 'r') as ECTText:
            text = ECTText.readlines()
            for line in text:
                line = line.lower()
                line = line.replace('\n', '')
                line_tokens = word_tokenize(line)
                for token in line_tokens:
                    # Remove stop words & punctuation marks
                    if token not in stopwords and token not in string.punctuation:
                        lemma = lemmatizer.lemmatize(token)
                        if lemma not in inverted_index.keys():
                            inverted_index[lemma] = []
                            tokens.add(lemma)
                            token_file.write(lemma)
                            token_file.write('\n')
                cnt += 1
                if DEBUG:
                    if cnt % 1000 == 0:
                        print("Tokenization - Steps done: {}".format(cnt))
        # break

    if DEBUG:
        print("Total number of tokens: {}".format(len(tokens)))


def prepare_inverted_index():

    # Currently merging two files with same initial ids
    iterations = 0

    for file in files:
        with open(os.path.join(DATA_PATH, file), 'r') as ECTText:
            counter = re.match(r'[0-9]{1,4}', file).group(0)
            counter = (int)(counter)
            text = ECTText.readlines()
            offset = 0
            for line in text:
                line = line.lower()
                line = line.replace('\n', '')
                line = line.split(' ')
                for pos in range(len(line)):
                    word = line[pos]
                    word = word.strip()
                    word = word.replace(',', '')
                    if word in tokens:
                        inverted_index[word].append((counter, pos + offset))
                offset += len(line)
        iterations = iterations + 1
        if DEBUG and iterations % 100 == 0:
            print('Inverted Index - Steps done: {}'.format(iterations))
        # break

    with open('inverted_index.json', 'w') as inv_idx:
        json.dump(inverted_index, inv_idx)


if __name__ == "__main__":
    get_tokens()
    prepare_inverted_index()
