from urllib import parse

import requests
from bs4 import BeautifulSoup
from notion_py.applications.read_scraper.helpers import try_twice


@try_twice
def get_yes24_url(book_name) -> str:
    book_name_encoded = parse.quote_plus(book_name, encoding='euc-kr')
    url_main_page = 'http://www.yes24.com'
    url = f"http://www.yes24.com/searchcorner/Search?keywordAd=&keyword=&domain=ALL&" \
          f"qdomain=%c5%eb%c7%d5%b0%cb%bb%f6&query={book_name_encoded}"

    response = requests.get(url)
    up_soup = BeautifulSoup(response, 'html5lib')

    tag_book = '#schMid_wrap > div:nth-child(4) > div.goodsList.goodsList_list > table > tbody > ' \
               'tr:nth-child(1) > td.goods_infogrp > p.goods_name.goods_icon > a'
    book = up_soup.select_one(tag_book)

    try:
        url_part = book.attrs['href']
        if 'yes24' not in url_part:
            url = url_main_page + url_part
        else:
            url = url_part
    except ValueError:
        return ''
    if '?OzSrank=1' in url:
        url = url[0:-len('?OzSrank=1')]
    print(url)
    return url


def scrap_yes24_metadata(url) -> dict:
    results = {}

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')

    tag_name = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2'
    tag_subname = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h3'
    tag_author = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > span.gd_pubArea > span.gd_auth > a'
    tag_author2 = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > span.gd_pubArea > span.gd_auth'
    tag_publisher = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > span.gd_pubArea > span.gd_pub > a'
    tag_page = '#infoset_specific > div.infoSetCont_wrap > div > table > tbody > tr:nth-child(2) > td'
    tag_cover_image = '#yDetailTopWrap > div.topColLft > div.gd_imgArea > span > em > img'
    tag_contents = '#infoset_toc > div.infoSetCont_wrap > div.infoWrap_txt'

    name = soup.select(tag_name)[0].text
    for char in '?!"':
        name = name.replace(char, '')

    subname = ''
    try:
        subname = soup.select_one(tag_subname).text
    except AttributeError:
        pass

    author = ''
    try:
        author = soup.select_one(tag_author).text
    except AttributeError:
        try:
            author = soup.select_one(tag_author2).text.strip('\n').strip().replace(' 저', '')
        except AttributeError:
            pass

    publisher = ''
    try:
        publisher = soup.select_one(tag_publisher).text
    except AttributeError:
        pass

    page = 0
    try:
        page_string = soup.select_one(tag_page).text
        if '쪽' in page_string:
            if '확인' not in page_string:
                page = int(page_string.split('|')[0].strip().replace('쪽', '').replace(',', ''))
    except AttributeError:
        pass

    cover_image = ''
    try:
        cover_image = str(soup.select_one(tag_cover_image))
        assert 'src' in cover_image
        cover_image = cover_image.split('src="')[-1].split('"/>')[0].strip()
    except AssertionError:
        pass

    contents = []
    try:
        contents_raw = soup.select_one(tag_contents).text
        for char in ['<B>', r'</b>', '<b>']:
            contents_raw = contents_raw.replace(char, '')
        contents_raw = contents_raw.strip()
        contents = contents_raw.split('<br/>')
    except AttributeError:
        pass

    results.update(
        name=name,
        subname=subname,
        author=author,
        publisher=publisher,
        page=page,
        cover_image=cover_image,
        contents=contents
    )
    return results
