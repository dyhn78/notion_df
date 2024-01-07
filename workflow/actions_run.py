import os
import subprocess
import sys
from pathlib import Path
from time import sleep

import psutil

from workflow import actions_exec, project_dir


def get_module_name(file_path: str) -> str:
    return '.'.join(Path(file_path).resolve().relative_to(project_dir).with_suffix('').parts)


this_module_name = get_module_name(__file__)
exec_module_name = get_module_name(actions_exec.__file__)

if __name__ == '__main__':
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            if process.cmdline()[:3] == [sys.executable, '-m', exec_module_name]:
                sys.stderr.write(f"{actions_exec.__name__} is already running.\n")
                sys.exit(1)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    proc = subprocess.run([sys.executable, '-m', exec_module_name],
                          env={**os.environ},
                          cwd=project_dir,
                          check=False)
    if proc.returncode != 0:
        sleep(600)
    else:
        sleep(5)
    os.execv(sys.executable, [sys.executable, '-m', this_module_name])
