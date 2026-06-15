from __future__ import annotations

import os
from pathlib import Path

from uri2ops.server.app import create_app


app = create_app(
    root=Path.cwd(),
    base_url=os.environ.get("URI2OPS_BASE_URL", "http://127.0.0.1:8791"),
)
