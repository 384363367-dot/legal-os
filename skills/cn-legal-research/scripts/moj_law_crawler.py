#!/usr/bin/env python3
"""Search the Ministry of Justice administrative-regulation library."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("moj-regulations", __doc__ or "Ministry of Justice adapter"))
