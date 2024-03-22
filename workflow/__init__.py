from pathlib import Path

_this = Path(__file__).resolve()
project_dir = _this.parents[1]
generated_dir = project_dir / 'generated'
generated_dir.mkdir(exist_ok=True)
backup_dir = generated_dir / 'backup'
backup_dir.mkdir(exist_ok=True)
log_dir = generated_dir / 'logs'
log_dir.mkdir(exist_ok=True)
output_dir = generated_dir / 'output'  # for scripts
output_dir.mkdir(exist_ok=True)
