from itertools import chain

from notion_df.entity import search_by_title
from workflow import backup_path
from workflow.action.migration_backup import MigrationBackupSaveAction
from workflow.block_enum import DatabaseEnum

if __name__ == '__main__':
    action = MigrationBackupSaveAction(backup_path)
    local_db_list = [db for db in search_by_title('', 'database')
                     if DatabaseEnum.from_entity(db) is None]
    print('#### [', *local_db_list, '] ####', sep='\n')
    action.process(chain.from_iterable(db.query() for db in local_db_list))
