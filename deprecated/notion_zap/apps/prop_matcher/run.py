from notion_zap.apps.prop_matcher.controllers.match_regulars import MatchController

if __name__ == '__main__':
    controller = MatchController()
    controller(request_size=5)
