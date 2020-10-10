# Reference - https://github.com/carstonhernke/scrape-earnings-transcripts/blob/master/scrape_earnings_calls.py

import requests
import time
import os
from bs4 import BeautifulSoup

''' Extract a specific page hosted on 'url' and write the contents of it to the article_name.html file '''

def grab_page(url, article_name):
    print("Attempting to get page: " + url)
    page = requests.get(url)
    page_html = page.text
    soup = BeautifulSoup(page_html, 'html.parser')
    content = soup.find("div", {"class": "sa-art article-width"})

    article_name = article_name.replace('/', '-')
    article_name = article_name.strip('-')

    filename = '{}'.format(article_name)
    file = open(os.path.join('ECT', filename.lower() + ".html"), 'w')
    file.write(str(content))
    file.close()
    print(filename.lower() + " Sucessfully saved")

''' Extract the list of arcticles on a given page and extract each of them sequentially '''

def process_list_page(page):
    origin_page = "https://seekingalpha.com/earnings/earnings-call-transcripts" + \
        "/" + str(page)
    print("Getting page " + origin_page)
    page = requests.get(origin_page)
    page_html = page.text
    soup = BeautifulSoup(page_html, 'html.parser')
    article_list = soup.find_all("li", {'class': 'list-group-item article'})
    for article in range(0, len(article_list)):
        page_url = article_list[article].find_all("a")[0].attrs['href']
        url = "https://seekingalpha.com" + page_url
        grab_page(url, page_url)
        time.sleep(0.5)


if __name__ == "__main__":
    if not os.path.exists('ECT'):
        os.makedirs('ECT')
    for page in range(1, 2):
        process_list_page(page)
