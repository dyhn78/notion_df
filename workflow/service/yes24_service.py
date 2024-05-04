from __future__ import annotations

import re
from typing import Optional
from urllib import parse

import requests
import requests.packages
from bs4 import BeautifulSoup

from notion_df.object.contents import Heading1BlockValue, ParagraphBlockValue, Heading2BlockValue, Heading3BlockValue, \
    BlockValue
from notion_df.object.rich_text import RichText

# noinspection PyUnresolvedReferences
# disable SSLError(1, '[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:997)') error for yes24.com
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


def get_yes24_detail_page_url(book_name: str) -> Optional[str]:
    if not book_name:
        return
    book_name = ''.join(filter(lambda x: str.isalnum(x) or x == ' ', book_name))
    book_name_encoded = parse.quote_plus(book_name, encoding='euc-kr')
    url_main_page = 'https://www.yes24.com'
    url = f"https://www.yes24.com/searchcorner/Search?keywordAd=&keyword=&domain=BOOK&" \
          f"qdomain=%c5%eb%c7%d5%b0%cb%bb%f6&query={book_name_encoded}"

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')

    tag_book = '#yesSchList > li:nth-child(1) > div > ' \
               'div.item_info > div.info_row.info_name > a.gd_name'
    book = soup.select_one(tag_book)

    try:
        url_part = book.attrs['href']
        if 'yes24' not in url_part:
            url = url_main_page + url_part
        else:
            url = url_part
    except (ValueError, AttributeError):
        return
    if '?OzSrank=1' in url:
        url = url[0:-len('?OzSrank=1')]
    return url


class Yes24ScrapResult:
    def __init__(self, detail_page_soup: BeautifulSoup):
        self.soup = detail_page_soup

    @classmethod
    def scrap(cls, detail_page_url: str) -> Yes24ScrapResult:
        response = requests.get(detail_page_url)
        return cls(BeautifulSoup(response.text, 'html5lib'))

    def get_true_name(self) -> Optional[str]:
        tag_name = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2'
        try:
            name = self.soup.select_one(tag_name).text.strip()
            for char in '?!"':
                name = name.replace(char, '')
            return name
        except AttributeError:
            pass

    def get_sub_name(self) -> Optional[str]:
        tag_sub_name = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h3'
        try:
            return self.soup.select_one(tag_sub_name).text.strip()
        except AttributeError:
            pass

    def get_author(self) -> Optional[str]:
        tag_author = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                     'span.gd_pubArea > span.gd_auth > a'
        try:
            return self.soup.select_one(tag_author).text.strip()
        except AttributeError:
            pass

        tag_author2 = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                      'span.gd_pubArea > span.gd_auth'
        try:
            author_raw = self.soup.select_one(tag_author2).text.strip()
            return author_raw.strip('\n').strip().replace(' 저', '')
        except AttributeError:
            pass

    def get_publisher(self) -> Optional[str]:
        tag_publisher = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                        'span.gd_pubArea > span.gd_pub > a'
        try:
            return self.soup.select_one(tag_publisher).text.strip()
        except AttributeError:
            pass

    def get_page_count(self) -> Optional[int]:
        tag_page = '#infoset_specific > div.infoSetCont_wrap > div > table > ' \
                   'tbody > tr:nth-child(2) > td'
        try:
            page_count_plus_etc = self.soup.select_one(tag_page).text
            if '쪽' in page_count_plus_etc and '확인' not in page_count_plus_etc:
                page_count_str = page_count_plus_etc.split('|')[0].strip()
                return int(''.join([char for char in page_count_str if char.isnumeric()]))
        except AttributeError:
            pass

    def get_cover_image_url(self) -> Optional[str]:
        tag_cover_image = '#yDetailTopWrap > div.topColLft > div.gd_imgArea > ' \
                          'span > em > img'
        try:
            cover_image = str(self.soup.select_one(tag_cover_image))
            if 'src' in cover_image:
                return cover_image.split('src="')[-1].split('"/>')[0].strip()
        except AttributeError:
            pass

    def get_contents(self) -> list[str]:
        tag_contents = '#infoset_toc > div.infoSetCont_wrap > div.infoWrap_txt'
        try:
            contents_html = self.soup.select_one(tag_contents).text
            return parse_contents(contents_html)
        except AttributeError:
            return []


def generate_tags(origin: set[str]) -> set[str]:
    origin.update(char.replace('<', '</') for char in origin.copy())
    origin.update(char.replace('>', '/>') for char in origin.copy())
    origin.update(char.upper() for char in origin.copy())
    return origin


CHARS_TO_DELETE = generate_tags({'<b>', '<strong>', r'\t', '__'})
CHARS_TO_SPLIT = generate_tags({'<br>', '\n',
                                # '|',
                                })
CHARS_TO_STRIP = generate_tags({'"', "'", ' ', '·'})
CHARS_TO_LSTRIP = generate_tags({'?'})
MAX_LINE_LENGTH = 2000  # due to Notion API


def parse_contents(contents_html: str):
    filtered = contents_html
    for char in CHARS_TO_DELETE:
        filtered = filtered.replace(char, ' ')
        filtered = filtered.strip()

    splited = [filtered]
    for char in CHARS_TO_SPLIT:
        prev = splited
        splited = []
        for line in prev:
            splited.extend(line.split(char))

    striped = []
    for line in splited:
        for char in CHARS_TO_STRIP:
            line = line.strip(char)
        for char in CHARS_TO_LSTRIP:
            line = line.lstrip(char)
        line = line.replace(" ", " ")
        if not line.replace(' ', ''):
            continue  # skip totally-blank lines
        striped.append(line)

    sliced = []
    for line in striped:
        line_frags = [line[i:i + MAX_LINE_LENGTH] for i in
                      range(0, len(line), MAX_LINE_LENGTH)]
        sliced.extend(line_frags)
    return sliced


VOLUME_KOR = re.compile(r"\d+권[.:]? ")
VOLUME_ENG = re.compile(r"VOLUME", re.IGNORECASE)

SECTION_KOR = re.compile(r"\d+부[.:]? ")
SECTION_ENG = re.compile(r"PART", re.IGNORECASE)

CHAPTER_KOR = re.compile(r"\d+장[.:]? ")
CHAPTER_ENG = re.compile(r"CHAPTER", re.IGNORECASE)

PASSAGE = re.compile(r"\d+[.:] ")


def get_block_value_of_contents_line(contents_line: str) -> BlockValue:
    rich_text = RichText.from_plain_text(contents_line)

    if VOLUME_KOR.findall(contents_line) or VOLUME_ENG.findall(contents_line):
        return Heading1BlockValue(rich_text, False)
    if SECTION_KOR.findall(contents_line) or SECTION_ENG.findall(contents_line):
        return Heading2BlockValue(rich_text, False)
    elif CHAPTER_KOR.findall(contents_line) or CHAPTER_ENG.findall(contents_line):
        return Heading3BlockValue(rich_text, False)
    return ParagraphBlockValue(rich_text)


if __name__ == '__main__':
    print(get_yes24_detail_page_url('무깟디마'))
