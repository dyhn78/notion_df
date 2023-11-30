import os
import subprocess
import sys
from pathlib import Path
from time import sleep

import psutil

from workflow import run_actions


def is_already_running():
    count = 0
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            if process.cmdline()[:2] == [sys.executable, run_actions.__file__]:
                count += 1
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return count > 1


if __name__ == '__main__':
    while True:
        if is_already_running():
            sys.stderr.write(f"{run_actions.__name__} is already running.\n")
            sys.exit(1)
        subprocess.run([sys.executable, run_actions.__file__],
                       env={**os.environ, 'PYTHONPATH': Path(__file__).resolve().parent})
        sleep(5)
