from pathlib import Path

_this = Path(__file__).resolve()
project_dir = _this.parents[1]
out_dir = project_dir / 'out'
out_dir.mkdir(exist_ok=True)
backup_dir = out_dir / 'backup'
backup_dir.mkdir(exist_ok=True)
log_dir = out_dir / 'logs'
log_dir.mkdir(exist_ok=True)
etc_dir = out_dir / 'etc'  # for scripts
etc_dir.mkdir(exist_ok=True)
