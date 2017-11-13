import requests
import re
import pandas as pd
from bs4 import BeautifulSoup

base_url = r'https://www.vouchercodes.co.uk/cats/food-and-drink/'
html = requests.get(base_url)
soup = BeautifulSoup(html.text, 'html.parser')
articles = soup.find_all('article')
box_re = re.compile(r'\n.+\t(?P<code>.+)\n.+')
article_re = re.compile(r'[\n|\t]+code[\n|\t]+(?P<offer>[^\t\n]+)[\n|\t]+[.|\n]+')


def _get_code(box_str):
    m = box_re.match(box_str)

    return m.group('code')


def _parse_article(atcl):
    m = article_re.match(atcl)

    return m.group('offer')


def item(iterable):
    if len(iterable) != 1:
        raise ValueError('Length of iterable isn\'t one.')

    return iterable[0]

offer_table = pd.DataFrame()
for article in articles:
    try:
        if article.attrs['data-offer-type'] != 'code':
            continue

        merchant = article['data-merchant']
        offer_id = article.attrs['data-offer-id']
        offer_url = base_url + '?rc={}'.format(offer_id)

        print merchant

        article_soup = BeautifulSoup(requests.get(offer_url).text, 'html.parser')

        code_box = item(article_soup.find_all('div', {'id': 'js-code-box'}))

        code = _get_code(code_box.text)
        off_details = _parse_article(article.text)

        offer_table = offer_table.append({'Offer': off_details, 'Merchant': merchant, 'Code': code}, ignore_index=True)
    except Exception, e:
        print 'Article failed with error: {}'.format(e)

try:
    offer_table.to_excel(r'C:\Users\Zach\Desktop\offers.csv', index=False)
except:
    print 'keema'
