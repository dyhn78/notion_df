import os
import subprocess
import sys
from pathlib import Path
from time import sleep

import psutil

from workflow import actions, project_dir

if __name__ == '__main__':
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            if process.cmdline()[:2] == [sys.executable, actions.__file__]:
                sys.stderr.write(f"{actions.__name__} is already running.\n")
                sys.exit(1)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    subprocess.run([sys.executable, actions.__file__],
                   env={**os.environ, 'PYTHONPATH': project_dir},
                   check=False)
    sleep(5)
    os.execv(sys.executable, [sys.executable, '-m', 'workflow.actions_run'])
