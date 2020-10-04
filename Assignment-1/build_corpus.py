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
import json
from bs4 import BeautifulSoup

DATA_PATH = './data/'

files = os.listdir(DATA_PATH)
files.sort()
total_files = len(files)

DEBUG = True

def populate_dates(soup, data_dict):

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
                    data_dict['Date'] = result.group(0)
                    assert data_dict['Date'] in para
                    break
        if found:
            break

def add_participant_category(pos, paragraphs, data_dict):
    new_added = 0
    for idx in range(pos + 1, len(paragraphs)):
        text = paragraphs[idx].text
        text = text.replace('–', '-')
        if '-' in text:
            name = text.split('-')[0].strip()
            if len(name) <= 100:
                data_dict['Participants'].append(name)
                new_added = new_added + 1
        else:
            break
    return new_added

# To-do: Some files have nested tags for the category. Fix it

def populate_participants(soup, data_dict):

    data_dict['Participants'] = []
    # paragraphs = soup.find_all('p', {'class': 'p'})
    paragraphs = soup.find_all('p')

    last_participant_pos = 0

    for idx in range(len(paragraphs)):
        text = paragraphs[idx].text.strip()
    
        if text.lower() == 'company participants':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text.lower() == 'conference call participants':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text.lower() == 'corporate participants':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text.lower() == 'company representatives':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text.lower() == 'executives':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text.lower() == 'analysts':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)

    return last_participant_pos

def build_textCorpus(soup, ECTText):
    text = soup.get_text()
    ECTText.write(text)
    ECTText.write('\n')
    pass

def populate_presentations(start, soup, data_dict):
    data_dict['Presentations'] = {}
    paragraphs = soup.find_all('p')

    name = ''

    for idx in range(start + 1, len(paragraphs)):
        para = paragraphs[idx]
        if para.has_attr('id'):
            break
        if len(para.contents) < 1:
            continue
        try:
            element = para.contents[0].contents
            name = para.text
            if type(name) != str:
                break
            if name not in data_dict['Presentations'].keys():
                data_dict['Presentations'][name] = []
        except AttributeError:
            dialogue = para.contents[0]
            if name != '':
                data_dict['Presentations'][name].append(dialogue)
            pass

        # if len(para.contents[0].contents):
        #     # Name of presenter
        #     name = para.contents[0].contents
        #     if name not in data_dict['Presentations'].keys():
        #         data_dict['Presentations'][name] = []
        # else:
        #     content = para.contents
        #     data_dict['Presentations'][name]
        #     pass            

def build_ECTNestedDict():

    # for cnt in range(total_files):
    #     data_dict[cnt] = {}

    ECTText = open('ECTText.txt', 'w')

    iterations = 0

    if not os.path.exists('ECTNestedDict'):
        os.makedirs('ECTNestedDict')

    for file in files:
        data_dict = {}
        abs_path = os.path.abspath(os.path.join(DATA_PATH, file))
        soup = BeautifulSoup(open(abs_path), "html.parser")
        counter = re.match(r'[0-9]{1,4}', file).group(0)
        counter = (int)(counter)

        # print(counter)

        build_textCorpus(soup, ECTText)
        populate_dates(soup, data_dict)
        last_participant_pos = populate_participants(soup, data_dict)
        populate_presentations(last_participant_pos, soup, data_dict)

        out_file = os.path.join('ECTNestedDict', os.path.splitext(file)[0] + '.json')

        with open(out_file, 'w') as outFile:
            json.dump(data_dict, outFile)

        iterations = iterations + 1
        if DEBUG and iterations % 100 == 0:
            print('ECTNestedDict - Steps done: {}'.format(iterations))

        # if DEBUG:
        #     print(counter)
        #     print(data_dict)

        # break

if __name__ == "__main__":
    build_ECTNestedDict()
