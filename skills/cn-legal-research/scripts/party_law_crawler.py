#!/usr/bin/env python3
"""Search publicly available Party-rule pages on 12371.cn."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("party-rules", __doc__ or "Party-rule adapter"))
