# from notion_zap.apps.externals.selenium import SeleniumScraper
from notion_zap.apps.prop_matcher.regulars import RegularMatchController

RegularMatchController(request_size=10).execute()
