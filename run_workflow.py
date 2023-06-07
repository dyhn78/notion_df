import os
import sys
from pathlib import Path
from time import sleep

import psutil


def is_already_running(script_path: Path):
    count = 0
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            if process.cmdline()[:2] in [[sys.executable, str(script_path)],
                                         [Path(sys.executable).name, script_path.name]]:
                count += 1
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return count > 1


if __name__ == '__main__':
    this_path = Path(__file__).resolve()
    if is_already_running(this_path):
        sys.stderr.write("Script is already running.\n")
        sys.exit(1)
    print(f'{"#" * 5 } Start.')

    from workflow.run import run_from_last_success

    log_enabled = run_from_last_success(False, False, this_path.parent / 'backup', True)
    print(f'{"#" * 5 } {"Done." if log_enabled else "No new record."}')
    if is_already_running(this_path):
        sys.stderr.write("Other script is running.\n")
        sys.exit(1)
    sleep(5)
    try:
        os.execv(sys.executable, [sys.executable, this_path])
    except OSError as e:
        print("Execution failed:", e)
