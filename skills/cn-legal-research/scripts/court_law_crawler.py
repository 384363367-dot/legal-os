#!/usr/bin/env python3
"""Search the Supreme People's Court public publications column."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("spc-publications", __doc__ or "Supreme People's Court adapter"))
