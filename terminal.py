import traceback
import datetime as dt

from notion_zap.apps.routines import main


with open('debug.log', 'w') as log:
    try:
        log.write(f"last execution: {dt.datetime.now()}")
        main.execute()
    except Exception as err:
        traceback.print_exc(file=log)
        raise err
# x = input("아무 키나 누르십시오...")
