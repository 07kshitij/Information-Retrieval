import os
import re
import json
import copy
import string
import time
import pickle5 as pickle
import numpy as np
from collections import OrderedDict
from numpy import dot
from numpy.linalg import norm
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

DATA_PATH = '../Dataset/'
LEADERS_PATH = '../Leaders.pkl'
STATIC_QUALITY_SCORE_PATH = '../StaticQualityScore.pkl'
CHAMPION_LIST_MAX_SIZE = 50
QUERY_MAX_SIZE = 10

stopwords = stopwords.words('english')
lemmatizer = WordNetLemmatizer()

tf_idf = {}
df_t = {}
tf_td = {}
idf_t = {}
InvertedPositionalIndex = OrderedDict()
ChampionListLocal = OrderedDict()
ChampionListGlobal = OrderedDict()
Static_Quality_Score = []
Leaders_List = []

def sortKey(s):
    return int(s.split('.')[0])

def un_pickle():

    with open(STATIC_QUALITY_SCORE_PATH, 'rb') as f:
        Static_Quality_Score = pickle.load(f)

    with open(LEADERS_PATH, 'rb') as f:
        Leaders_List = pickle.load(f)

    return Static_Quality_Score, Leaders_List

def tf_idf_score():

    files = os.listdir(DATA_PATH)
    files.sort(key=sortKey)
    N = len(files)
    counter = 0

    for file_name in files:

        counter += 1
        file_path = os.path.abspath(os.path.join(DATA_PATH, file_name))
        soup = BeautifulSoup(open(file_path), "html.parser")

        docId = int(file_name.replace('.html', ''))

        # Lowercase
        file_contents = soup.get_text().replace('\n', ' ').lower().strip()

        # Remove Punctuation
        for punctuation in string.punctuation:
            file_contents = file_contents.replace(punctuation, ' ')

        # Remove extra whitespaces
        file_contents = file_contents.replace('  ', ' ')

        # Lemmatize and tokenize
        for token in word_tokenize(file_contents):
            if token not in stopwords:
                token = lemmatizer.lemmatize(token)
                try:
                    tf_td[(token, docId)] += 1
                except KeyError:
                    tf_td[(token, docId)] = 1
                    try:
                        df_t[token].append(docId)
                    except KeyError:
                        df_t[token] = [docId]

        if counter % 100 == 0:
            print('Steps Done: {}'.format(counter))

    for token, docId in tf_td.keys():
        idf_t[token] = np.log10(N / len(df_t[token]))
        tf_td[(token, docId)] = np.log10(1 + tf_td[(token, docId)])
        tf_idf[(token, docId)] = tf_td[(token, docId)] * idf_t[token]

        try:
            InvertedPositionalIndex[(token, idf_t[token])].append((docId, tf_td[(token, docId)]))
        except KeyError:
            InvertedPositionalIndex[(token, idf_t[token])] = [(docId, tf_td[(token, docId)])]

        try:
            ChampionListLocal[token].append(docId)
            ChampionListGlobal[token].append(docId)
        except KeyError:
            ChampionListLocal[token] = [docId]
            ChampionListGlobal[token] = [docId]

    for token in ChampionListLocal.keys():
        len_list = min(CHAMPION_LIST_MAX_SIZE, len(ChampionListLocal[token]))
        ChampionListLocal[token] = sorted(ChampionListLocal[token], key=lambda x : tf_td[(token, x)], reverse=True)
        ChampionListLocal[token] = ChampionListLocal[token][:len_list]

    for token in ChampionListGlobal.keys():
        len_list = min(CHAMPION_LIST_MAX_SIZE, len(ChampionListGlobal[token]))
        ChampionListGlobal[token] = sorted(ChampionListGlobal[token], key=lambda x : Static_Quality_Score[x] + tf_idf[(token, x)], reverse=True)
        ChampionListGlobal[token] = ChampionListGlobal[token][:len_list]

    with open('../ChampionListLocal.json', 'w') as f:
        json.dump(ChampionListLocal, f, indent=2)

    with open('../ChampionListGlobal.json', 'w') as f:
        json.dump(ChampionListGlobal, f, indent=2)

    print(len(InvertedPositionalIndex.keys()))

    return N

def tf_idf_vector(query, docId):
    vector = []
    for word, idf in InvertedPositionalIndex.keys():
        if (word, docId) in tf_idf.keys():
            vector.append(tf_idf[(word, docId)])
        else:
            vector.append(0)
    return vector

def local_championlist_vector(query, docId):
    vector = []
    for word, idf in InvertedPositionalIndex.keys():
        if (word, docId) in tf_idf.keys():
            vector.append(tf_idf[(word, docId)])
        else:
            vector.append(0)
    return vector

def global_championlist_vector(query, docId):
    vector = []
    for word, idf in InvertedPositionalIndex.keys():
        if (word, docId) in tf_idf.keys():
            vector.append(tf_idf[(word, docId)])
        else:
            vector.append(0)
    return vector

leaders_vector = {}
norm_leader = {}
followers_vector = {}
Followers_List = {}

def compute_followers(N):

    for leader in Leaders_List:
        vector = []
        for word, idf in InvertedPositionalIndex.keys():
            if (word, leader) in tf_idf.keys():
                vector.append(tf_idf[(word, leader)])
            else:
                vector.append(0)
        leaders_vector[leader] = np.array(vector)
        norm_leader[leader] = norm(leaders_vector[leader])

    for docId in range(N):
        if docId not in Leaders_List:
            vector = []
            for word, idf in InvertedPositionalIndex.keys():
                if (word, docId) in tf_idf.keys():
                    vector.append(tf_idf[(word, docId)])
                else:
                    vector.append(0)
            followers_vector[docId] = np.array(vector)

            n = norm(followers_vector[docId])

            if n:
                max_score = 0; L = None
                for leader in Leaders_List:
                    if norm_leader[leader]:
                        score = dot(followers_vector[docId], leaders_vector[leader])
                        score /= n
                        score /= norm_leader[leader]
                        if score > max_score:
                            max_score = score; L = leader
                try:
                    Followers_List[L].append(docId)
                except KeyError:
                    Followers_List[L] = [docId]

def answer_query(query_file, N):

    with open(query_file) as f:
        queries = f.readlines()
        for query in queries:
            query = query.replace('\n', ' ').strip().lower()
            for punctuation in string.punctuation:
                query = query.replace(punctuation, ' ')
            query = query.replace('  ', ' ')

            query_vector = []
            words = []

            for word in word_tokenize(query):
                if word not in stopwords:
                    word = lemmatizer.lemmatize(word)
                    words.append(word)

            for word, idf in InvertedPositionalIndex.keys():
                if word in words:
                    query_vector.append(idf)
                else:
                    query_vector.append(0)

            scores = []

            query_vector = np.array(query_vector)


            for docId in range(N):
                ss = np.array(tf_idf_vector(words, docId))

                if norm(ss) != 0 and norm(query_vector) != 0:            
                    score = dot(query_vector, ss) / (norm(query_vector) * norm(ss))
                    scores.append((docId, score))
                    # print(docId, ss, score)

            scores = sorted(scores, key=lambda x: x[1], reverse=True)
            scores = scores[:min(10, len(scores))]
            print(scores)

            cache = []
            scores = []

            for word in words:
                for docId in ChampionListLocal[word]:
                    if docId in cache:
                        continue
                    cache.append(docId)
                    ss = np.array(local_championlist_vector(words, docId))
                    if norm(ss) != 0 and norm(query_vector) != 0:            
                        score = dot(query_vector, ss) / (norm(query_vector) * norm(ss))
                        scores.append((docId, score))

            scores = sorted(scores, key=lambda x: x[1], reverse=True)
            scores = scores[:min(10, len(scores))]
            print(scores)

            cache = []
            scores = []

            for word in words:
                for docId in ChampionListGlobal[word]:
                    if docId in cache:
                        continue
                    cache.append(docId)
                    ss = np.array(global_championlist_vector(words, docId))
                    if norm(ss) != 0 and norm(query_vector) != 0:            
                        score = dot(query_vector, ss) / (norm(query_vector) * norm(ss))
                        scores.append((docId, score))

            scores = sorted(scores, key=lambda x: x[1], reverse=True)
            scores = scores[:min(10, len(scores))]
            print(scores)

            n = norm(query_vector)
            compute_followers(N)

            # print(Followers_List)

            scores = []

            for leader in Leaders_List:
                score = dot(query_vector, leaders_vector[leader])
                if norm_leader[leader] and n:
                    score /= n
                    score /= norm_leader[leader]
                    scores.append((leader, score))

            scores = sorted(scores, key=lambda x: x[1], reverse=True)
            L_q = scores[0][0]
            ss = scores[0]

            scores = []
            scores.append(ss)

            for follower in Followers_List[L_q]:
                score = dot(query_vector, followers_vector[follower])
                if norm(followers_vector[follower]) and n:
                    score /= n
                    score /= norm(followers_vector[follower])
                    scores.append((follower, score))

            scores = sorted(scores, key=lambda x: x[1], reverse=True)
            scores = scores[:min(10, len(scores))]
            print(scores)

if __name__ == "__main__":
    Static_Quality_Score, Leaders_List = un_pickle()
    N = tf_idf_score()
    answer_query('query.txt', N)