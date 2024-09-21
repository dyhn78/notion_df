from itertools import chain

from app import backup_dir
from app.action.migration_backup import MigrationBackupSaveAction
from app.my_block import DatabaseEnum
from notion_df.entity import search_by_title

if __name__ == '__main__':
    action = MigrationBackupSaveAction(backup_dir)
    local_db_list = [db for db in search_by_title('', 'database')
                     if DatabaseEnum.from_entity(db) is None]
    print('#### [', *local_db_list, '] ####', sep='\n')
    action.process_pages(chain.from_iterable(db.query() for db in local_db_list))
