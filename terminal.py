from notion_py.applications.log_editor.request import connect_to_naljja, connect_to_gigan
from notion_py.applications.read_scraper import update_ilggi

update_ilggi()
connect_to_naljja(check_only_past_x_days=7)
connect_to_gigan(check_only_past_x_days=7)

close_program = input("작업 완료. 아무 키나 누르십시오...")
