#!/bin/python3
from pathlib import Path

Path('boundaries.py').symlink_to('../../bin/main.py')

import main

main.update_index_files()
