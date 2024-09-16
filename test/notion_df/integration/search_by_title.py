from pprint import pprint, pformat

from notion_df.entity import search_by_title

if __name__ == '__main__':
    result = search_by_title("", None, 'descending', 10)[:10]
    print(pformat(result))
