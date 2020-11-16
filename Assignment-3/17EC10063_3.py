import sys, os
import numpy as np
from string import punctuation
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from copy import deepcopy
from sklearn.metrics import f1_score
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.neighbors import KNeighborsClassifier

stopwords = stopwords.words('english')
lemmatizer = WordNetLemmatizer()

DEBUG = True

class kNN_classifier:
    def __init__(self, data_path, out_file):
        self.data_path = data_path
        self.out_file = out_file
        self.tokens = []
        self.feature_idx_map = {}
        self.tf_idf = {}
        self.df_t = {}
        self.tf_td = {}
        self.idf_t = {}
        self.TOTAL_FILE_LEN = 0
        self.mean_c1 = []
        self.mean_c2 = []

    def prepare_feature_map(self):
        for pos, token in enumerate(self.tokens):
            self.feature_idx_map[token] = pos

    def prepare_count_matrix(self):
        classes = os.listdir(self.data_path)
        self.X_train = []; self.y_train = []
        self.X_test = []; self.y_test = []
        for className in classes:
            class_path = os.path.join(self.data_path, className)
            if className == 'class1' or className == 'class2':
                classID = int(className[-1])
                data_folders = os.listdir(class_path)
                for data_folder in data_folders:
                    data_path = os.path.join(class_path, data_folder)
                    files = os.listdir(data_path)
                    files.sort(key=lambda x: int(x))
                    X = []; y = []
                    for file_ in files:
                        text = open(os.path.join(data_path, file_), errors='replace').read()
                        text = text.lower()
                        feature_vector = [0] * len(self.tokens)
                        for _ in punctuation:
                            text = text.replace(_, ' ')
                        text = text.replace('  ',' ')
                        tokens = word_tokenize(text)
                        for token in tokens:
                            if token not in stopwords:
                                token = lemmatizer.lemmatize(token)
                                try:
                                    pos = self.feature_idx_map[token]
                                    feature_vector[pos] += 1
                                except KeyError:
                                    pass
                        X.append(feature_vector)
                        y.append(classID)

                    if data_folder == 'train':
                        self.X_train.extend(X)
                        self.y_train.extend(y)
                    else:
                        self.X_test.extend(X)
                        self.y_test.extend(y)

        if DEBUG:
            print('Construction of feature matrix complete')
        self.X_train = np.array(self.X_train)
        self.y_train = np.array(self.y_train)
        self.X_test = np.array(self.X_test)
        self.y_test = np.array(self.y_test)

    def prepare_tf_idf_vectors(self):
        transformer = TfidfTransformer()
        self.X_train = transformer.fit_transform(self.X_train).toarray()
        self.X_test = transformer.transform(self.X_test).toarray()

    def read_dataset(self):
        classes = os.listdir(self.data_path)
        for className in classes:
            class_path = os.path.join(self.data_path, className)
            if className == 'class1' or className == 'class2':
                self.tokens.extend(self.read_class(class_path))
        self.tokens = list(set(self.tokens))
        self.tokens.sort()
        if DEBUG:
            print('Total Features: {}'.format(len(self.tokens)))

    def read_class(self, class_path):
        data_folders = os.listdir(class_path)
        for data_folder in data_folders:
            data_path = os.path.join(class_path, data_folder)
            if data_folder == 'train':
                return self.process_data(data_path)

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

    @staticmethod
    def inner_product(x, y):
        return 1 - np.dot(x, y)

    def run_kNN(self, K, out_file):
        
        results = []
        for k in K:
            kNN = KNeighborsClassifier(n_neighbors=k, metric=self.inner_product)
            kNN.fit(self.X_train, self.y_train)
            y_predict = kNN.predict(self.X_test)
            score = f1_score(self.y_test, y_predict, average='macro')
            results.append(score)
            if DEBUG:
                print('k = {}, f1_score = {}'.format(k, score))

        result_file = open(out_file, 'w', encoding='utf-8')
        result_file.write("NumFeature")

        for k in K:
            result_file.write(' {}'.format(k))
        result_file.write('\n')

        result_file.write("KNeighborsClassifier")
        for result in results:
            result_file.write(' {}'.format(round(result, 6)))

if __name__ == "__main__":
    data_path, out_file = sys.argv[1], sys.argv[2]
    K = [1, 10, 50]
    kNN = kNN_classifier(data_path, out_file)
    kNN.read_dataset()
    kNN.prepare_feature_map()
    kNN.prepare_count_matrix()
    kNN.prepare_tf_idf_vectors()
    kNN.run_kNN(K, out_file)
