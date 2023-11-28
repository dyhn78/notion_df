import subprocess
import sys
from pathlib import Path
from time import sleep

import psutil

from workflow import run_actions


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
    while True:
        if is_already_running(Path(__file__).resolve()):
            sys.stderr.write(f"{__name__} is already running.\n")
            sys.exit(1)
        subprocess.run([sys.executable, run_actions.__file__])
        sleep(5)
