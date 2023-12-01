from pathlib import Path

_this = Path(__file__).resolve()
project_dir = _this.parents[1]
backup_dir = project_dir / 'backup'
backup_dir.mkdir(exist_ok=True)
log_dir = project_dir / 'logs'
log_dir.mkdir(exist_ok=True)
data_dir = project_dir / 'data'  # for scripts. TODO: fix naming.
data_dir.mkdir(exist_ok=True)
