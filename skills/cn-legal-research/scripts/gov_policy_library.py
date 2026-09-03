#!/usr/bin/env python3
"""Search the State Council Policy Document Library."""
from __future__ import annotations

from site_cli import main_for_source


if __name__ == "__main__":
    raise SystemExit(main_for_source("state-council-policy", __doc__ or "Policy adapter"))
