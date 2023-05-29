from pathlib import Path

_this = Path(__file__).resolve()
project_path = _this.parents[1]
data_path = _this / 'data'
