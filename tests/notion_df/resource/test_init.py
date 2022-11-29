from notion_df.resource.resource import Resource


def test_resource():
    assert Resource.find_type({'type': 'checkbox', 'checkbox': True}) == ('checkbox',)
    assert Resource.find_type({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}) == ('mention', 'user')
