import os
import sys
from pathlib import Path
from time import sleep

import psutil


def is_already_running(script_name):
    count = 0
    for process in psutil.process_iter(['name', 'cmdline']):
        if script_name in process.cmdline():
            count += 1
    return count > 1


if __name__ == '__main__':
    if is_already_running(os.path.basename(__file__)):
        print("Script is already running.")
        sys.exit(1)
    print(f'{"#" * 5 } Start.')

    from workflow.run import run_from_last_success

    log_enabled = run_from_last_success(print_body=False, create_window=False)
    print(f'{"#" * 5 } {"Done." if log_enabled else "No new record."}')
    sleep(5)
    try:
        os.execv(sys.executable, [sys.executable, (Path(__file__).resolve())])
    except OSError as e:
        print("Execution failed:", e)
