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
import string

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

    # Mark the starting index for the next task
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
    text = re.sub(u"(\u2018|\u2019)", "'", text)
    ECTText.write(text)
    ECTText.write('\n')
    pass

def populate_presentations(start, soup, data_dict):
    data_dict['Presentations'] = {}
    paragraphs = soup.find_all('p')

    name = ''

    # Start from the ending of participants section (pointed by start)
    for idx in range(start + 1, len(paragraphs)):
        para = paragraphs[idx]
        # Filter start of QnA section
        if para.has_attr('id'): 
            break
        # Filter tags like <p></p>
        if len(para.contents) < 1:
            continue
        # Check if the tag is a name or dialogue 
        try:
            element = para.contents[0].contents
            name = para.text
            if name == 'Question-and-Answer Session':
                break
            # Currently ignoring tags like <strong><span>Name</span></strong>
            if type(name) != str:
                break
            name = re.sub(u"(\u2018|\u2019)", "'", name)
            if name not in data_dict['Presentations'].keys():
                data_dict['Presentations'][name] = []
        except AttributeError:
            dialogue = para.contents[0]
            dialogue = re.sub(u"(\u2018|\u2019)", "'", dialogue)
            if name != '':
                data_dict['Presentations'][name].append(dialogue)
            pass

def search_text(soup, data_dict, counter):
    return

def build_questionnaire(soup, data_dict):
    data_dict['Questionnaire'] = {}
    paragraphs = soup.find_all('p')

    found = False

    for idx in range(len(paragraphs)):
        para = paragraphs[idx]
        if para.has_attr('id'):
            if para['id'] == 'question-answer-session':
                found = True
                count = 0
                name = ''
                last_name = ''
                for pos in range(idx + 1, len(paragraphs)):
                    para = paragraphs[pos]
                    if len(para.contents) < 1:
                        continue
                    pass
                    try:
                        element = para.contents[0].content
                        name = para.text
                        if type(name) != str:
                            name = para.contents[0].text
                            if type(name) != str:
                                break
                            if name[0:3] == 'Q -':
                                name = name[3:]
                        else:
                            if name[0:3] == 'Q -':
                                name = name[3:]
                        name = name.strip()
                    except AttributeError:
                        response = para.contents[0]
                        response = re.sub(u"(\u2018|\u2019)", "'", response)
                        if name != '':
                            if name != last_name:
                                data_dict['Questionnaire'][count] = {}
                                data_dict['Questionnaire'][count]['Speaker'] = str(name)
                                data_dict['Questionnaire'][count]['Remark'] = str(response)
                                count = count + 1
                            else:
                                prev = data_dict['Questionnaire'][count - 1]['Remark']
                                data_dict['Questionnaire'][count - 1]['Remark'] = prev + str(response)
                            last_name = name
        if found:
            break

    if not found:
        return            

def build_ECTNestedDict():

    # for cnt in range(total_files):
    #     data_dict[cnt] = {}

    # ECTText = open('ECTText.txt', 'w')

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

        # build_textCorpus(soup, ECTText)
        populate_dates(soup, data_dict)
        last_participant_pos = populate_participants(soup, data_dict)
        populate_presentations(last_participant_pos, soup, data_dict)
        build_questionnaire(soup, data_dict)

        out_file = os.path.join('ECTNestedDict', os.path.splitext(file)[0] + '.json')

        with open(out_file, 'w') as outFile:
            json.dump(data_dict, outFile)

        iterations = iterations + 1
        if DEBUG and iterations % 100 == 0:
            print('ECTNestedDict - Steps done: {}'.format(iterations))

        # if DEBUG:
        #     print(counter, data_dict)

        # break

if __name__ == "__main__":
    build_ECTNestedDict()

# BUGS FIXED

# **** BUG FIX NEEDED ASAP ***
# 1. Words like I've are written as I\u2019ve in the json. Investigate the issue and fix ASAP
#    Need this working as it impacts tokenization
#       Sol - \u2019 is unicode for left '. Replace them using regex