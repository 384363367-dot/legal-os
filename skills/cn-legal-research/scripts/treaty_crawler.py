#!/usr/bin/env python3
"""Search the Ministry of Foreign Affairs treaty database."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("mfa-treaty", __doc__ or "Treaty adapter"))
