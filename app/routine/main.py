# TODO: use supervisord. https://chatgpt.com/c/6797165b-942c-8004-95b2-bd91c66157c1
import os
import subprocess
import sys
from pathlib import Path
from time import sleep

import psutil

import app.routine.task
from app import project_dir


def get_module_name(file_path: str) -> str:
    return ".".join(
        Path(file_path).resolve().relative_to(project_dir).with_suffix("").parts
    )


main_module_argv = [sys.executable, "-m", get_module_name(__file__)]
task_module_argv = [sys.executable, "-m", get_module_name(app.routine.task.__file__)]

if __name__ == "__main__":
    for process in psutil.process_iter(["name", "cmdline"]):
        try:
            command = " ".join(process.cmdline())
            if " ".join(task_module_argv) in command:
                sys.stderr.write(
                    f"Aborting: task module is already running on another process."
                    f" {command=}\n"
                )
                sys.exit(1)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    proc = subprocess.run(
        task_module_argv, env={**os.environ}, cwd=project_dir, check=False
    )
    if proc.returncode != 0:
        sleep(600)
    else:
        sleep(5)
    os.execv(sys.executable, main_module_argv)
