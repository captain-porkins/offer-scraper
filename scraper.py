import requests
import re
from bs4 import BeautifulSoup

base_url = r'https://www.vouchercodes.co.uk/cats/food-and-drink/'
html = requests.get(base_url)
soup = BeautifulSoup(html.text, 'html.parser')
articles = soup.find_all('article')
for article in articles:
    if article.attrs['data-offer-type'] != 'code':
        continue
    offer_id = article.attrs['id'].split('-')[-1]
    offer_url = base_url + '?rc={}'.format(offer_id)
    article_soup = BeautifulSoup(requests.get(offer_url).text, 'html.parser')

    code_box_list = article_soup.find_all('div', {'id': 'js-code-box'})
    assert len(code_box_list) == 1
    code_box = code_box_list[0]

    # ToDo: strip out code with regex on code_box.text


    print 'roti'
