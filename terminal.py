import traceback
import datetime as dt

from notion_zap.apps.routines import main


log = open('debug.log', 'w', encoding='utf-8')
log.write(f"last execution: {dt.datetime.now()}")
try:
    main.execute()
except Exception as err:
    traceback.print_exc(file=log)
    log.close()
    raise err
# x = input("아무 키나 누르십시오...")
