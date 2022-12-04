from notion_zap.apps.media_scraper.controllers.scrap_regulars import RegularScrapController


if __name__ == '__main__':
    # controller = RegularScrapController(targets={'metadata'})
    # controller.fetch(title='헬스의 정석')
    controller = RegularScrapController()
    controller.fetch(request_size=3)
    controller.process()
    # RegularScrapController(tasks={'metadata'}).execute(request_size=5)
