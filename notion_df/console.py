from pprint import pprint

from notion_df.entity import Namespace, Database

if __name__ == '__main__':
    namespace = Namespace()
    database: Database = namespace.database(
        'https://www.notion.so/dyhn/d020b399cf5947a59d11a0b9e0ea45d0?v=b7bc6354436448c5ad285c89089f0a35&pvs=4')
    response = database.retrieve()
    pprint(response)
