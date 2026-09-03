#!/usr/bin/env python3
"""Search the State Taxation Administration public rules library."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("tax-rules", __doc__ or "Tax rules adapter"))
