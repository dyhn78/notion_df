import os
import subprocess
import sys
from pathlib import Path
from time import sleep

import psutil

from workflow import actions_exec, project_dir

if __name__ == '__main__':
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            if process.cmdline()[:2] == [sys.executable, actions_exec.__file__]:
                sys.stderr.write(f"{actions_exec.__name__} is already running.\n")
                sys.exit(1)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    proc = subprocess.run([sys.executable, actions_exec.__file__],
                          env={**os.environ, 'PYTHONPATH': project_dir},
                          check=False)
    if proc.returncode != 0:
        sleep(600)
    else:
        sleep(5)
    this_module_name = '.'.join(Path(__file__).resolve().relative_to(project_dir).with_suffix('').parts)
    os.execv(sys.executable, [sys.executable, '-m', this_module_name])
