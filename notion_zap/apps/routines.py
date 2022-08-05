from notion_zap.apps.helpers.deal_exception import ExceptionLogger


@ExceptionLogger()
def main():
    from notion_zap.apps.media_scraper.controllers.scrap_regulars import RegularScrapController
    from notion_zap.apps.prop_matcher.controllers.match_regulars import MatchController

    controller = MatchController()
    controller(request_size=20)
    print('=' * 40)
    controller = RegularScrapController(targets={'metadata', 'gy'})
    controller(request_size=5)


def manual():
    from notion_zap.apps.media_scraper import \
        ReadingTableDuplicateRemover
    from notion_zap.apps.prop_matcher.controllers.build_calendar import CalendarBuildController
    from notion_zap.apps.prop_matcher.controllers.resolve_sync import SyncResolveController

    CalendarBuildController(fetch_empties=True).execute()
    ReadingTableDuplicateRemover().execute(request_size=0)
    SyncResolveController(date_range=0).execute()
