from notion_zap.apps.media_scraper.regulars \
    import ReadingDBScrapController


ReadingDBScrapController(tasks={'bookstore'}, title='대서울길').execute(request_size=1)

close_program = input("작업 완료. 아무 키나 누르십시오...")
