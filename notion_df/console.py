from pprint import pprint
from uuid import UUID

from notion_df.entity import Namespace, Page

if __name__ == '__main__':
    namespace = Namespace()
    page: Page = namespace.page(UUID(''))
    response = page.retrieve()
    pprint(response)
