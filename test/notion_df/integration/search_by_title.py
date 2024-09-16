from pprint import pprint, pformat

from notion_df.entity import search_by_title

if __name__ == '__main__':
    result = search_by_title("", None, 'descending', page_size=5)
    pprint(result)
    pprint(result[:10])
