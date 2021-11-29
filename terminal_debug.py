from notion_zap.apps.routines import main

try:
    main.execute()
except Exception as e:
    print(e)
    x = input("아무 키나 누르십시오...")
