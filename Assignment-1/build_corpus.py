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


participant_names = []


def add_participant_category(pos, paragraphs, data_dict):
    new_added = 0
    for idx in range(pos + 1, len(paragraphs)):
        text = ''
        try:
            # Check for elements inside span
            element = paragraphs[idx].contents[0].contents[0]
            text = paragraphs[idx].get_text()
        except AttributeError:
            text = paragraphs[idx].get_text()
        if text == " ":
            continue
        text = text.replace('–', '-')
        if '-' in text:
            first_name = text.split(' - ')[0].strip()
            name = text.strip()
            if len(name) <= 200:
                name = replace_unicode(name)
                first_name = replace_unicode(first_name)
                participant_names.append(first_name)
                data_dict['Participants'].append(name)
                new_added = new_added + 1
        else:
            break
    return new_added


def populate_participants(soup, data_dict):

    data_dict['Participants'] = []
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
            last_participant_pos = idx + \
                add_participant_category(idx, paragraphs, data_dict)
        if text == 'conference call participants':
            last_participant_pos = idx + \
                add_participant_category(idx, paragraphs, data_dict)
        if text == 'corporate participants':
            last_participant_pos = idx + \
                add_participant_category(idx, paragraphs, data_dict)
        if text == 'company representatives':
            last_participant_pos = idx + \
                add_participant_category(idx, paragraphs, data_dict)
        if text == 'executives':
            last_participant_pos = idx + \
                add_participant_category(idx, paragraphs, data_dict)
        if text == 'analysts':
            last_participant_pos = idx + \
                add_participant_category(idx, paragraphs, data_dict)

    return last_participant_pos


def populate_presentations(start, soup, data_dict, counter, participants):
    data_dict['Presentations'] = {}
    paragraphs = soup.find_all('p')

    # Add anonymous names
    participants.append('Operator')
    participants.append('operator')
    participants.append('Unidentified Analyst')
    participants.append('Unidentified Company Representative')

    name = ''
    nested_name = ''
    taking_inline = True
    taking_nested = False

    # print(participants)

    # Start from the ending of participants section (pointed by start)
    for idx in range(start + 1, len(paragraphs)):
        para = paragraphs[idx]
        # print(para)
        # Filter start of QnA section
        if para.has_attr('id'):
            break
        if para.text == 'Question-and-Answer Session':         # Filter start of QnA section
            break
        if len(para.contents) < 1:                             # Filter tags like <p></p>
            continue
        # Check if the tag is a name or dialogue
        try:
            # print(counter, para)
            element = para.contents[0].contents[0]
            name = para.get_text().strip()
            if name == 'Question-and-Answer Session':
                break
            try:
                element = element.contents[0]
                nested_name = para.get_text().strip()
                nested_name = replace_unicode(nested_name)
                taking_inline = False
                taking_nested = True
                if nested_name not in data_dict['Presentations'].keys() and nested_name in participants:
                    data_dict['Presentations'][nested_name] = []
            except AttributeError:
                dialogue = para.get_text()
                dialogue = replace_unicode(dialogue)
                if nested_name != '' and dialogue != " " and taking_nested and nested_name in participants:
                    data_dict['Presentations'][nested_name].append(dialogue)
            name = replace_unicode(name)
            if name not in data_dict['Presentations'].keys() and taking_inline and name in participants:
                data_dict['Presentations'][name] = []
                taking_nested = False
        except AttributeError:
            dialogue = para.get_text()
            dialogue = replace_unicode(dialogue)
            if name != '' and dialogue != " " and taking_inline and name in participants:
                data_dict['Presentations'][name].append(dialogue)
        except IndexError:
            continue


def build_questionnaire(soup, data_dict, counter, participants):
    data_dict['Questionnaire'] = {}
    paragraphs = soup.find_all('strong')

    # Add anonymous names
    participants.append('Operator')
    participants.append('operator')
    participants.append('Unidentified Analyst')
    participants.append('Unidentified Company Representative')

    qNa_started = False

    position = 1

    for para in paragraphs:
        name = para.get_text().strip()
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
            if splits[1] in participants:
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


def write_date(value):

    text = 'Date\n'
    text += value
    text += '\n'
    return text


def write_participants(list_of_participants):

    text = 'Participants\n'

    for name in list_of_participants:
        text += name
        text += '\n'

    return text


def write_presentation(presentations):

    text = 'Presentations\n'

    for key, value in presentations.items():
        text += key + '\n'
        for dialogue in value:
            text += dialogue + '\n'

    return text


def write_questionnaire(questionnaire):

    text = 'Questionnaire\n'

    for key, value in questionnaire.items():
        text += str(key) + '\n'
        speaker = value['Speaker']
        text += speaker + '\n'
        remark = value['Remark']
        text += remark + '\n'

    return text


def build_textCorpus(soup, data_dict):

    text = ''
    if 'Date' in data_dict.keys():
        text += write_date(data_dict['Date'])
    text += write_participants(data_dict['Participants'])
    text += write_presentation(data_dict['Presentations'])
    text += write_questionnaire(data_dict['Questionnaire'])

    return text


def build_ECTNestedDict():

    iterations = 0

    if not os.path.exists('ECTNestedDict'):
        os.makedirs('ECTNestedDict')

    if not os.path.exists('ECTText'):
        os.makedirs('ECTText')

    for file in files:
        data_dict = {}
        abs_path = os.path.abspath(os.path.join(DATA_PATH, file))
        soup = BeautifulSoup(open(abs_path), "html.parser")
        counter = re.match(r'[0-9]{1,4}', file).group(0)
        counter = (int)(counter)

        populate_dates(soup, data_dict)
        last_participant_pos = populate_participants(soup, data_dict)
        participants = copy.deepcopy(participant_names)

        populate_presentations(last_participant_pos, soup,
                               data_dict, counter, participants)
        build_questionnaire(soup, data_dict, counter, participants)

        text_file = build_textCorpus(soup, data_dict)

        out_json_file = os.path.join(
            'ECTNestedDict', os.path.splitext(file)[0] + '.json')

        out_text_file = os.path.join(
            'ECTText', os.path.splitext(file)[0] + '.txt')

        with open(out_json_file, 'w') as outFile:
            json.dump(data_dict, outFile)

        with open(out_text_file, 'w') as outFile:
            outFile.write(text_file)

        iterations = iterations + 1
        if DEBUG and iterations % 100 == 0:
            print('ECTNestedDict - Steps done: {}'.format(iterations))

        # if DEBUG:
        #     print(counter, data_dict)
        # break


if __name__ == "__main__":
    build_ECTNestedDict()
