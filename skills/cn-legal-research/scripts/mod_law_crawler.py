#!/usr/bin/env python3
"""Search public national-defence regulation pages on mod.gov.cn."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("mod-regulations", __doc__ or "National-defence adapter"))
