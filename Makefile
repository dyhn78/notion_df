test:  test.mypy test.pylint test.unit

test.mypy:
	mypy notion_df/

test.pylint:
	pylint notion_df/

test.unit:
	pytest tests/
