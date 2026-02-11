"""Allow running scholar_translator as a module: python -m scholar_translator"""

import sys

from scholar_translator.cli import main

sys.exit(main())