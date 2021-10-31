# insert this at <client.py>
"""
from pprint import pprint

for data, datastr in zip([method, path, query, body],
                         ['method', 'path', 'query', 'body']):
    print(f'--- {str(datastr).upper()} : ')
    pprint(data, width=100)
"""
