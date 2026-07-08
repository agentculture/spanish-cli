"""Entry point for ``python -m spanish``."""

from __future__ import annotations

import sys

from spanish.cli import main

if __name__ == "__main__":
    sys.exit(main())
