import requests
from bs4 import BeautifulSoup

from .parse_contents import parse_contents


def scrap_yes24_metadata(url: str) -> dict:
    results = {}

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')

    tag_name = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2'
    tag_subname = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h3'
    tag_author = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                 'span.gd_pubArea > span.gd_auth > a'
    tag_author2 = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                  'span.gd_pubArea > span.gd_auth'
    tag_publisher = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                    'span.gd_pubArea > span.gd_pub > a'
    tag_page = '#infoset_specific > div.infoSetCont_wrap > div > table > ' \
               'tbody > tr:nth-child(2) > td'
    tag_cover_image = '#yDetailTopWrap > div.topColLft > div.gd_imgArea > ' \
                      'span > em > img'
    tag_contents = '#infoset_toc > div.infoSetCont_wrap > div.infoWrap_txt'

    name = ''
    try:
        name = soup.select_one(tag_name).text
        for char in '?!"':
            name = name.replace(char, '')
    except AttributeError:
        pass

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
            author = soup.select_one(tag_author2).text.strip('\n').strip().replace(' 저',
                                                                                   '')
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
                page = int(
                    page_string.split('|')[0].strip().replace('쪽', '').replace(',', ''))
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
        contents = parse_contents(contents_raw)
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
