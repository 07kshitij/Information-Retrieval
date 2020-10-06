import os
import re
import json
import copy
import string
from bs4 import BeautifulSoup

DATA_PATH = './data/'

files = os.listdir(DATA_PATH)
files.sort()
total_files = len(files)

DEBUG = True

def replace_unicode(response):
    response = re.sub(u"(\u2018|\u2019)", "'", response)
    response = re.sub(u"(\u2013|\u2014)", "-", response)
    response = re.sub(u"(\u2026)", "...", response)
    response = re.sub(u"(\u00e4)", "a", response)
    response = re.sub(u"(\u20ac)", "Euro ", response)
    response = re.sub(u"(\u00e9)", "e", response)
    response = re.sub(u"(\u00fc)", "u", response)
    return response

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
        text = ''
        try:
            element = paragraphs[idx].contents[0].contents[0] # Check for elements inside span
            text = str(element)
        except AttributeError:
            text = paragraphs[idx].get_text()
        if text == " ":
            continue
        text = text.replace('–', '-')
        if '-' in text:
            name = text.split('-')[0].strip()
            if len(name) <= 100:
                name = replace_unicode(name)
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
        text = paragraphs[idx].text
        if type(text) != str:   # span tag exists
            text = paragraphs[idx].contents[0].text.strip()
        else:
            text = text.strip()
    
        text = text.lower()

        if text == 'company participants':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text == 'conference call participants':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text == 'corporate participants':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text == 'company representatives':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text == 'executives':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)
        if text == 'analysts':
            last_participant_pos = idx + add_participant_category(idx, paragraphs, data_dict)


    return last_participant_pos

def build_textCorpus(soup, ECTText):
    text = soup.get_text()
    text = replace_unicode(text)
    ECTText.write(text)
    ECTText.write('\n')
    pass

def populate_presentations(start, soup, data_dict, counter):
    data_dict['Presentations'] = {}
    paragraphs = soup.find_all('p')

    name = ''
    nested_name = ''
    taking_inline = True
    taking_nested = False

    # Start from the ending of participants section (pointed by start)
    for idx in range(start + 1, len(paragraphs)):
        para = paragraphs[idx]
        if para.has_attr('id'):                                # Filter start of QnA section
            break
        if para.text == 'Question-and-Answer Session':         # Filter start of QnA section
            break
        if len(para.contents) < 1:                             # Filter tags like <p></p>
            continue
        # Check if the tag is a name or dialogue 
        try:
            # print(counter, para)
            element = para.contents[0].contents[0]
            name = para.text
            if name == 'Question-and-Answer Session':
                break
            try:
                element = element.contents[0]
                nested_name = str(element)
                nested_name = replace_unicode(nested_name)
                taking_inline = False
                taking_nested = True
                if nested_name not in data_dict['Presentations'].keys():
                    data_dict['Presentations'][nested_name] = []
            except AttributeError:
                dialogue = para.contents[0].contents[0]
                dialogue = replace_unicode(dialogue)
                if nested_name != '' and dialogue != " " and taking_nested:
                    data_dict['Presentations'][nested_name].append(dialogue)
            name = replace_unicode(name)
            if name not in data_dict['Presentations'].keys() and taking_inline:
                data_dict['Presentations'][name] = []
                taking_nested = False
        except AttributeError:
            dialogue = para.contents[0]
            dialogue = replace_unicode(dialogue)
            if name != '' and dialogue != " " and taking_inline:
                data_dict['Presentations'][name].append(dialogue)
        except IndexError:
            continue

def search_text(soup, data_dict, counter):
    return

def build_questionnaire(soup, data_dict, counter, participants):
    data_dict['Questionnaire'] = {}
    paragraphs = soup.find_all('strong')

    # Add anonymous names
    participants.append('Operator')
    participants.append('operator')
    participants.append('Unidentified Analyst')
    participants.append('Unidentified Company Representative')

    qNa_started = False

    position = 0

    for para in paragraphs:
        name = para.get_text()
        if 'Question-and' in name or 'Question-' in name:
            qNa_started = True
            continue

        if not qNa_started:
            continue

        person = ""
        if name in participants:
            person = name
        elif len(name.split('-')) > 1:
            splits = name.split('-')
            splits[0] = splits[0].strip()
            splits[1] = splits[1].strip()
            if splits[0] in participants:
                person = splits[0]
            elif splits[1] in participants:
                person = splits[1]
        person = person.strip()
        if person == "" or person == " " or name == None:
            continue

        para_parent = para.parent
        response = ""

        for sibling in para_parent.next_siblings:
            if sibling.name == None:
                continue
            children = sibling.find_all('strong', recursive=False)
            if sibling.get_text() == " ":
                continue
            if len(children):
                break
            response += str(sibling.get_text())

        person = replace_unicode(person)
        response = replace_unicode(response)    

        data_dict['Questionnaire'][position] = {
            'Speaker': person,
            'Remark': response
        }

        position += 1

def build_ECTNestedDict():

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

        build_textCorpus(soup, ECTText)
        populate_dates(soup, data_dict)
        last_participant_pos = populate_participants(soup, data_dict)
        populate_presentations(last_participant_pos, soup, data_dict, counter)
        participants = copy.deepcopy(data_dict['Participants'])
        build_questionnaire(soup, data_dict, counter, participants)

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
