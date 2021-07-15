from notion_py.applications.log_editor.request import connect_to_naljja, connect_to_gigan
from notion_py.applications.read_scraper import update_reading_list

connect_to_naljja()
connect_to_gigan()
update_reading_list()

# close_program = input("작업 완료. 아무 키나 누르십시오...")
