from datetime import timedelta
from pathlib import Path
from typing import Optional

from loguru import logger

from workflow import log_dir
from workflow.actions import actions
from workflow.core.action import run_from_last_success


def get_latest_log_path() -> Optional[Path]:
    log_path_list = sorted(log_dir.iterdir())
    if not log_path_list:
        return
    return log_path_list[-1]


if __name__ == '__main__':
    logger.add((get_latest_log_path() or log_dir / '{time}.log'),
               level='DEBUG', rotation='100 MB', retention=timedelta(weeks=2))
    logger.info(f'{"#" * 5} Start.')
    new_record = run_from_last_success(actions=actions, update_last_success_time=True)
    logger.info(f'{"#" * 5} {"Done." if new_record else "No new record."}')
