default_filter = {'database_id': 'TEST_DATABASE_ID',
                  'filter_manager': {
                      'or': [{
                          'property': '이름',
                          'text': {'contains': '1'}
                      },
                          {
                              'property': '이름',
                              'text': {'contains': '2'}
                          }]
                  }}
