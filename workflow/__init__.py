from pathlib import Path

_this = Path(__file__).resolve()
project_path = _this.parents[1]
backup_path = project_path / 'backup'
data_path = _this / 'data'  # for scripts. TODO: fix naming.
