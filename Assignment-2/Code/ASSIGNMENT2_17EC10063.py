import os
import sys
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
DEBUG = False

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

leaders_vector = {}
norm_leader = {}
followers_vector = {}
Followers_List = {}

''' Sort the files in lexicographical order of the index in file name '''


def sortKey(s):
    return int(s.split('.')[0])


''' Return the Leaders and Static_Quality_Score list from the .pkl files '''


def unpickle_dataset():

    with open(STATIC_QUALITY_SCORE_PATH, 'rb') as f:
        Static_Quality_Score = pickle.load(f)

    with open(LEADERS_PATH, 'rb') as f:
        Leaders_List = pickle.load(f)

    return Static_Quality_Score, Leaders_List


''' Case folding, punctutation removal on text '''


def preprocess_text(text):
    text = text.replace('\n', ' ').strip().lower()     # To Lowercase
    for punctuation in string.punctuation:             # Remove Punctuation
        text = text.replace(punctuation, ' ')
    # Remove extra whitespaces
    text = text.replace('  ', ' ')
    return text


''' Builds the InvertedPositionalIndex, ChampionListLocal & ChampionListGlobal dictionaries'''


def build_score_dict():

    files = os.listdir(DATA_PATH)
    files.sort(key=sortKey)
    N = len(files)
    counter = 0

    for file_name in files:

        counter += 1
        file_path = os.path.abspath(os.path.join(DATA_PATH, file_name))
        soup = BeautifulSoup(open(file_path), "html.parser")

        docId = int(file_name.replace('.html', ''))

        file_contents = soup.get_text()
        file_contents = preprocess_text(file_contents)

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

        if DEBUG and counter % 100 == 0:
            print('Steps Done: {}'.format(counter))

    for token, docId in tf_td.keys():
        idf_t[token] = np.log10(N / len(df_t[token]))
        tf_td[(token, docId)] = np.log10(1 + tf_td[(token, docId)])
        tf_idf[(token, docId)] = tf_td[(token, docId)] * idf_t[token]

        try:
            InvertedPositionalIndex[(token, idf_t[token])].append(
                (docId, tf_td[(token, docId)]))
        except KeyError:
            InvertedPositionalIndex[(token, idf_t[token])] = [
                (docId, tf_td[(token, docId)])]

        try:
            ChampionListLocal[token].append(docId)
            ChampionListGlobal[token].append(docId)
        except KeyError:
            ChampionListLocal[token] = [docId]
            ChampionListGlobal[token] = [docId]

    for token in ChampionListLocal.keys():
        len_list = min(CHAMPION_LIST_MAX_SIZE, len(ChampionListLocal[token]))
        ChampionListLocal[token] = sorted(
            ChampionListLocal[token], key=lambda x: tf_td[(token, x)], reverse=True)
        ChampionListLocal[token] = ChampionListLocal[token][:len_list]

    for token in ChampionListGlobal.keys():
        len_list = min(CHAMPION_LIST_MAX_SIZE, len(ChampionListGlobal[token]))
        ChampionListGlobal[token] = sorted(
            ChampionListGlobal[token], key=lambda x: Static_Quality_Score[x] + tf_idf[(token, x)], reverse=True)
        ChampionListGlobal[token] = ChampionListGlobal[token][:len_list]

    if DEBUG:
        print('Tokens: {}'.format(len(InvertedPositionalIndex.keys())))

    return N


''' Writes the answer for a particular score type to the result file '''


def write_answer(result_file, scores):
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    scores = scores[:min(QUERY_MAX_SIZE, len(scores))]
    idx = 0
    delimiter = ','
    for docId, score in scores:
        result_file.write('<{},{}>'.format(docId, score))
        idx += 1
        if idx == len(scores):
            delimiter = '\n'
        result_file.write(delimiter)
    return


''' Returns the word vector for the document '''


def get_doc_vector(docId):
    if docId in Leaders_List:
        doc_vector = leaders_vector[docId]
    else:
        doc_vector = followers_vector[docId]
    return doc_vector


''' Computes the tf_idf score for the given query_vector '''


def get_tf_idf_score(query_vector, N, result_file):
    tf_idf_scores = []
    norm_query = norm(query_vector)

    for docId in range(N):
        doc_vector = get_doc_vector(docId)
        if norm(doc_vector) != 0 and norm(query_vector) != 0:
            score = dot(query_vector, doc_vector) / (norm_query * norm(doc_vector))
            tf_idf_scores.append((docId, score))

    write_answer(result_file, tf_idf_scores)


''' Computes the local champion list score for the given query_vector '''


def get_local_champion_list_score(query_terms, query_vector, result_file):
    cache = []
    local_champion_list_scores = []
    norm_query = norm(query_vector)
    for word in query_terms:
        for docId in ChampionListLocal[word]:
            if docId in cache:
                continue
            cache.append(docId)
            doc_vector = get_doc_vector(docId)
            if norm(doc_vector) != 0 and norm(query_vector) != 0:
                score = dot(query_vector, doc_vector) / (norm_query * norm(doc_vector))
                local_champion_list_scores.append((docId, score))

    write_answer(result_file, local_champion_list_scores)


''' Computes the global champion list score for the given query_vector '''


def get_global_champion_list_score(query_terms, query_vector, result_file):
    cache = []
    global_champion_list_scores = []
    norm_query = norm(query_vector)

    for word in query_terms:
        for docId in ChampionListGlobal[word]:
            if docId in cache:
                continue
            cache.append(docId)
            doc_vector = get_doc_vector(docId)
            if norm(doc_vector) != 0 and norm(query_vector) != 0:
                score = dot(query_vector, doc_vector) / (norm_query * norm(doc_vector))
                global_champion_list_scores.append((docId, score))

    write_answer(result_file, global_champion_list_scores)


''' Computes the cluster pruning score for the given query_vector '''


def get_cluster_pruning_score(query_vector, result_file):
    norm_query = norm(query_vector)
    cluster_pruning_scores = []

    for leader in Leaders_List:
        if norm_leader[leader] and norm_query:
            score = dot(
                query_vector, leaders_vector[leader]) / (norm_query * norm_leader[leader])
            cluster_pruning_scores.append((leader, score))

    cluster_pruning_scores = sorted(
        cluster_pruning_scores, key=lambda x: x[1], reverse=True)
    best_leader = cluster_pruning_scores[0][0]
    leader_score = cluster_pruning_scores[0]

    cluster_pruning_scores = []
    cluster_pruning_scores.append(leader_score)

    for follower in Followers_List[best_leader]:
        if norm(followers_vector[follower]) and norm_query:
            score = dot(query_vector, followers_vector[follower]) / (norm_query * norm(followers_vector[follower]))
            cluster_pruning_scores.append((follower, score))

    write_answer(result_file, cluster_pruning_scores)

    result_file.write('\n')


''' Cluster Pruning - Computes the list of followers and prepares the document vectors '''


def cluster_pruning(N):

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

            norm_follower = norm(followers_vector[docId])

            if norm_follower:
                max_score = 0
                L = None
                for leader in Leaders_List:
                    if norm_leader[leader]:
                        score = dot(
                            followers_vector[docId], leaders_vector[leader]) / (norm_follower * norm_leader[leader])
                        if score > max_score:
                            max_score = score
                            L = leader
                try:
                    Followers_List[L].append(docId)
                except KeyError:
                    Followers_List[L] = [docId]


''' Computes the 4 required scores for queries in the given query_file '''


def answer_query(query_file, N):

    result_file = open('RESULTS2_17EC10063.txt', 'w')

    with open(query_file, 'r') as f:
        queries = f.readlines()
        for query in queries:
            original_query = copy.deepcopy(query)
            result_file.write(original_query + '\n')

            query = preprocess_text(query)

            query_vector = []
            query_terms = []

            for word in word_tokenize(query):
                if word not in stopwords:
                    word = lemmatizer.lemmatize(word)
                    query_terms.append(word)

            for word, idf in InvertedPositionalIndex.keys():
                if word in query_terms:
                    query_vector.append(idf)
                else:
                    query_vector.append(0)

            query_vector = np.array(query_vector)

            get_tf_idf_score(query_vector, N, result_file)
            get_local_champion_list_score(
                query_terms, query_vector, result_file)
            get_global_champion_list_score(
                query_terms, query_vector, result_file)
            get_cluster_pruning_score(query_vector, result_file)

    result_file.close()


if __name__ == "__main__":
    start = time.time()
    Static_Quality_Score, Leaders_List = unpickle_dataset()

    N = build_score_dict()
    cluster_pruning(N)

    query_file = sys.argv[1]
    answer_query(query_file, N)

    if DEBUG:
        print('Time: {}'.format(time.time() - start))
