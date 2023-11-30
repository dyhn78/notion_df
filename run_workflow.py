import os
import subprocess
import sys
from pathlib import Path
from time import sleep

import psutil

from workflow import run_actions


def is_already_running():
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            if process.cmdline()[:2] == [sys.executable, run_actions.__file__]:
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False


if __name__ == '__main__':
    if is_already_running():
        sys.stderr.write(f"{run_actions.__name__} is already running.\n")
        sys.exit(1)
    with Path('log.txt').open() as log_file:
        subprocess.run([sys.executable, run_actions.__file__],
                       env={**os.environ, 'PYTHONPATH': Path(__file__).resolve().parent},
                       stdout=log_file)
    sleep(5)
    os.execv(sys.executable, [sys.executable, Path(__file__).resolve()])
