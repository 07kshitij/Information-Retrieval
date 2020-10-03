# --- TO FIX ---

#  -- No file --
# 1260 {} Not present
# 1659 {} -- Ignore (Invalid date)
# 2130 {} Not present
# 2220 {} Not present
# 3687 {} -- Ignore (Invalid date)
# 4711 {} Not present
# 4712 {} Not present

# -- Repeated files --
# [3872, 3873, 3874, 3875, 3876]

# -- No participants --
# 719 {'Date': 'August 17, 2020', 'Participants': []} -- inside span
# 1663 {'Date': 'August 5, 2020', 'Participants': []} -- No participant
# 2707 {'Date': 'August 4, 2020', 'Participants': []} -- inside span
# 3906 {'Date': 'July 28, 2020', 'Participants': []} -- No spaces
# 4508 {'Date': 'July 7, 2020', 'Participants': []} -- inside span

import os
import re
from bs4 import BeautifulSoup
from collections import OrderedDict

DATA_PATH = './data/'

files = os.listdir(DATA_PATH)
files.sort()
total_files = len(files)

LOG_OUTPUT = True
data_dict = OrderedDict()

def populate_dates(counter, soup):

    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    paragraphs = soup.find_all('p', {'class': 'p'})

    for loop in range(min(5, len(paragraphs))):
        para = paragraphs[loop].text
        # Remove possible multiple spaces
        para = ' '.join(para.split())
        tokens = para.split()
        found = False
        for month in months:
            if month in tokens:
                pattern = month + r' [0-9]{1,2}, [1-9][0-9]{1,3}'
                result = re.search(pattern, para)
                if result:
                    found = True
                    data_dict[counter]['Date'] = result.group(0)
                    assert data_dict[counter]['Date'] in para
                    break
        if found:
            break

def add_participant_category(pos, paragraphs, counter):
    for idx in range(pos + 1, len(paragraphs)):
        text = paragraphs[idx].text
        text = text.replace('–', '-')
        if '-' in text:
            name = text.split('-')[0].strip()
            if len(name) <= 100:
                data_dict[counter]['Participants'].append(name)
        else:
            break

# To-do: Some files have nested tags for the category. Fix it

def populate_participants(counter, soup):

    data_dict[counter]['Participants'] = []
    paragraphs = soup.find_all('p', {'class': 'p'})

    for idx in range(len(paragraphs)):
        text = paragraphs[idx].text.strip()
    
        if text.lower() == 'company participants':
            add_participant_category(idx, paragraphs, counter)
        if text.lower() == 'conference call participants':
            add_participant_category(idx, paragraphs, counter)
        if text.lower() == 'corporate participants':
            add_participant_category(idx, paragraphs, counter)
        if text.lower() == 'company representatives':
            add_participant_category(idx, paragraphs, counter)
        if text.lower() == 'executives':
            add_participant_category(idx, paragraphs, counter)
        if text.lower() == 'analysts':
            add_participant_category(idx, paragraphs, counter)

def build_corpus():

    for cnt in range(total_files):
        data_dict[cnt] = {}

    iterations = 0

    for file in files:
        abs_path = os.path.abspath(os.path.join(DATA_PATH, file))
        soup = BeautifulSoup(open(abs_path), "html.parser")
        counter = re.match(r'[0-9]{1,4}', file).group(0)
        counter = (int)(counter)

        populate_dates(counter, soup)
        populate_participants(counter, soup)

        iterations = iterations + 1
        if LOG_OUTPUT and iterations % 100 == 0:
            print('Steps done: {}'.format(iterations))

    if LOG_OUTPUT:
        for key, value in data_dict.items():
            if 'Participants' in value.keys() and len(value['Participants']) == 0:
                print(key, value)
            elif not ('Participants' in value.keys()):
                print(key, value)

if __name__ == "__main__":
    build_corpus()