import sys, os
import numpy as np
from string import punctuation
from sklearn.naive_bayes import MultinomialNB, BernoulliNB
from sklearn.feature_selection import mutual_info_classif
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from copy import deepcopy

stopwords = stopwords.words('english')
lemmatizer = WordNetLemmatizer()

class Naive_Bayes:
    def __init__(self, data_path, out_file):
        self.data_path = data_path
        self.out_file = out_file
        self.top_features_count = [1, 10, 100, 1000, 10000]
        self.tokens_1 = []
        self.tokens_2 = []

    def get_features(self):
        tokens = deepcopy(self.tokens_1)
        tokens.extend(self.tokens_2)
        self.features = list(set(tokens))
        print(len(self.features))

    def generate_feature_matrix(self):
        return

    def read_dataset(self):
        classes = os.listdir(self.data_path)
        for className in classes:
            class_path = os.path.join(self.data_path, className)
            if className == 'class1':
                self.tokens_1 = self.read_class(class_path)
            if className == 'class2':
                self.tokens_2 = self.read_class(class_path)
        print(len(self.tokens_1), len(self.tokens_2))

    def read_class(self, class_path):
        data_files = os.listdir(class_path)
        for data_file in data_files:
            data_path = os.path.join(class_path, data_file)
            if data_file == 'train':
                return self.process_data(data_path)
            else:
                pass

    @staticmethod
    def process_data(data_path):
        files = os.listdir(data_path)
        features = set()
        files.sort(key=lambda x: int(x))
        for file_ in files:
            text = open(os.path.join(data_path, file_), errors='replace').read()
            text = text.lower()

            for _ in punctuation:
                text = text.replace(_, ' ')
            text = text.replace('  ',' ')

            tokens = word_tokenize(text)

            for token in tokens:
                if token not in stopwords:
                    token = lemmatizer.lemmatize(token)
                    features.add(token)
        return list(features)

    def fit_MultinomialNB(self):
        return

    def fit_BernoulliNB(self):
        return

    def get_mutual_information(self, X, y):
        return mutual_info_classif(X, y, discrete_features=True, random_state=0)

    def run_NB(self):
        for top_features_count in self.top_features_count:
            pass

if __name__ == "__main__":
    data_path, out_file = sys.argv[1], sys.argv[2]
    NB = Naive_Bayes(data_path, out_file)
    NB.read_dataset()
    NB.get_features()