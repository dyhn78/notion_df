import traceback

from notion_zap.apps.routines import main

try:
    main.execute()
except Exception as err:
    with open('debug.log', 'w') as log:
        traceback.print_exc(file=log)
        # raise err
# x = input("아무 키나 누르십시오...")
