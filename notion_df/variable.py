from __future__ import annotations

import os
from datetime import timezone, timedelta
from typing import Final

my_tz = timezone(timedelta(hours=9))
print_width = 120
token: Final[str] = os.getenv('NOTION_TOKEN')  # TODO: support multiple token
