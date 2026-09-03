#!/usr/bin/env python3
"""Search the Ministry of Ecology and Environment public rules pages."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("mee-regulations", __doc__ or "Ecology and environment adapter"))
