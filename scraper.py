# -*- coding: utf-8 -*-
import re
import smtplib
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

box_re = re.compile(r'\n.+\t(?P<code>.+)\n.+')
article_re = re.compile(r'[\n|\t]+code[\n|\t]+(?P<offer>[^\t\n]+)[\n|\t]+[.|\n]+')


def get_code(box_str):
    m = box_re.match(box_str)

    return m.group('code')


def parse_article(atcl):
    m = article_re.match(atcl)

    return m.group('offer')


def item(iterable):
    if len(iterable) != 1:
        raise ValueError('Length of iterable isn\'t one.')

    return iterable[0]


def sort_metric(offer_string, typical_purchase=50):
    """
    Tries to deduce how 'good' the offer is (how much you get off) by looking for money vals in the string
    :param offer_string:
    :param typical_purchase:
    :return:
    """
    money_vals = [float(v) for v in re.findall(r'\xa3([0-9]+)', offer_string)]
    percent_vals = [float(v) for v in re.findall(r'([0-9]+)%', offer_string)]

    try:
        return item(percent_vals) / 100.0
    except ValueError:
        if len(money_vals) == 1:
            return money_vals[0] / typical_purchase
        elif len(money_vals) == 2:
            return min(money_vals) / max(money_vals)
        else:
            # ToDo: Review default?
            return 0.1


def url_genny(base_url, max_n=100):
    # Ensure arguments make sense
    if max_n < 1:
        raise ValueError('max_n should be greater than 1')
    # Start generating, start by returning base_url then iterating through other pages, starting with page 2
    yield base_url
    i = 2
    while True:
        if i == max_n:
            break
        elif i > max_n:
            raise RuntimeError('Generator has passed max_n')

        yield base_url + '?page={}'.format(i)
        i += 1


class SafeSSL(smtplib.SMTP_SSL):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def send_email(email_to, subject, body, user, password, email_from=None, server_str='smtp.gmail.com', port=465,
               txt_type='html'):
    email_from = email_from or user
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = ', '.join(email_to)
    msg.attach(MIMEText(body, txt_type, _charset='utf-8'))

    with SafeSSL(server_str, port) as server:
        server.ehlo()
        server.login(user, password)
        server.sendmail(email_from, email_to, msg.as_string())

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('user', type=str)
arg_parser.add_argument('password', type=str)
arg_parser.add_argument('email_list', type=str, nargs='+')
args = arg_parser.parse_args()

vc_url = r'https://www.vouchercodes.co.uk/cats/food-and-drink/'
offer_table = pd.DataFrame()

for url in url_genny(vc_url):
    print url
    html = requests.get(url).text

    if 'page not found' in html:
        break

    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find_all('article')
    for article in articles:
        try:
            if article.attrs['data-offer-type'] != 'code':
                continue

            merchant = article['data-merchant']
            offer_id = article.attrs['data-offer-id']
            offer_url = vc_url + '?rc={}'.format(offer_id)

            article_soup = BeautifulSoup(requests.get(offer_url).text, 'html.parser')

            code_box = item(article_soup.find_all('div', {'id': 'js-code-box'}))
            code = get_code(code_box.text)
            off_details = parse_article(article.text)

            offer_table = offer_table.append({'Offer': off_details, 'Merchant': merchant, 'Code': code,
                                             'sorter': sort_metric(off_details, typical_purchase=50)},
                                             ignore_index=True)
        except Exception, e:
            print 'Article failed with error: {}'.format(e)

output_path = r'C:\Users\Zach\Desktop\offers_{:Y-m-%d_%H%M%S}.csv'.format(datetime.now())
offer_table = offer_table.sort_values('sorter', ascending=False)
offer_table = offer_table.drop('sorter', axis=1)
offer_table.to_csv(output_path, index=False, encoding='utf-8')


send_email(args.email_list, 'Offers {:%Y-%m-%d}'.format(datetime.now()),
           offer_table.to_html(justify='center', index=False), args.user, args.password)
