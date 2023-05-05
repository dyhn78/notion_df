from pprint import pprint

from notion_df.entity import Namespace, Page
from notion_df.util.misc import UUID

if __name__ == '__main__':
    namespace = Namespace()
    page: Page = namespace.page(UUID(''))
    response = page.retrieve()
    pprint(response)
