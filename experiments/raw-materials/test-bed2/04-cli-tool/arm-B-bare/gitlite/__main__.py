"""支持 `python -m gitlite`。"""

import sys

from .cli import main

sys.exit(main(sys.argv[1:]))
