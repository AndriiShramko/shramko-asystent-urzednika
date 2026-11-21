"""`python -m converter ...` runs the command line of the converter (app.cli, work package WP-F1)."""
import sys

from app.cli import main

if __name__ == "__main__":
    sys.exit(main())
