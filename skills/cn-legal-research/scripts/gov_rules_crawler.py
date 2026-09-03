#!/usr/bin/env python3
"""Search the public National Rules Library through its official entry point."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("gov-rules", __doc__ or "National rules adapter"))
