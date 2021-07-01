from abc import abstractmethod

from db_handler.handler_base import BaseHandler


class Decorator(BaseHandler):
    def __init__(self):
        self._apply = []

    def clear(self):
        self._apply = []

    @property
    def apply(self):
        return self._apply

    def block_type(self, block_type):
        return {
            'object': 'block',
            'type': block_type,
            block_type: self.apply
        }


class RichTextHandler(Decorator):
    def append_text(self, content, link=None):
        self._apply.append(self.__text(content, link))

    def append_equation(self, expression: str):
        self._apply.append(self.__equation(expression))

    def append_mention_page(self, page_id):
        self._apply.append(self.__mention_page(page_id, 'page'))

    def append_mention_database(self, database_id):
        self._apply.append(self.__mention_page(database_id, 'database'))

    def append_mention_user(self, user_id):
        self._apply.append(self.__mention_page(user_id, 'user'))

    def append_mention_date(self, start_date, end_date=None):
        self._apply.append(self.__mention_date(start_date, end_date))

    def appendleft_text(self, content, link=None):
        self._apply.insert(0, self.__text(content, link))

    def appendleft_equation(self, expression: str):
        self._apply.insert(0, self.__equation(expression))

    def appendleft_mention_page(self, page_id):
        self._apply.insert(0, self.__mention_page(page_id, 'page'))

    def appendleft_mention_database(self, database_id):
        self._apply.insert(0, self.__mention_page(database_id, 'database'))

    def appendleft_mention_user(self, user_id):
        self._apply.insert(0, self.__mention_page(user_id, 'user'))

    def appendleft_mention_date(self, start_date, end_date=None):
        self._apply.insert(0, self.__mention_date(start_date, end_date))

    @classmethod
    def __type(cls, prop_type, value):
        return {
            prop_type: value,
            'type': prop_type
        }

    @classmethod
    def __text(cls, content, link=None):
        value = {'content': content}
        if link:
            value[link] = link
        return cls.__type('text', value)

    @classmethod
    def __equation(cls, expression: str):
        equation = {'expression': expression},
        return cls.__type('equation', equation)

    @classmethod
    def __mention_page(cls, target_id, target_class):
        """
        {'mention': {'page': {'id': 'e15c62be-b9e4-4bb5-9b62-9220804fe93f'},
                     'type': 'page'},
         'type': 'mention'}
        """
        assert target_class in ["user", "page", "database"]
        mention = {
            target_class: {'id': target_id},
            'type': target_class
        }
        return cls.__type('mention', mention)

    @classmethod
    def __mention_date(cls, start_date, end_date=None):
        """
        :param start_date, end_date: ISO8601 date and time
        """
        date = {
            'start': start_date,
            'end': end_date
        }
        mention = {
            'date': date,
            'type': 'date'
        }
        return cls.__type('mention', mention)


"""            
TEST_DATABASE_ID = "5c021bea3e2941f39bff902cb2ebfe47"
notion.pages.create(
                    parent={
                        'database_id': TEST_DATABASE_ID,
                        'type': 'database_id'
                    },
                    properties={
                        'title': [
                                  {
                                    'text': {
                                      'content': 'Tuscan Kale',
                                    },
                                  },
                                ],
                    })
"""
"""
{
    object: 'block',
    type: 'heading_2',
    heading_2: {
      'text': [
        {
          'type': 'text',
          'text': {
            'content': 'Lacinato kale',
          },
        },
      ],
    },
}
"""