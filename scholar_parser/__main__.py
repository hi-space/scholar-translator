"""Allow running scholar_parser as a module: python -m scholar_parser"""

import sys

from scholar_parser.cli import main

sys.exit(main())