#!/bin/python3
from pathlib import Path
import os

Path('boundaries.py').symlink_to('../../bin/main.py')

os.system("chmod +x main.py")

if not os.path.exists("../../var/bnd-repo/tmp"):
    Path("../../var/bnd-repo/tmp").mkdir()

if not os.path.exists("../../var/bnd-repo/repos"):
    Path("../../var/bnd-repo/repos").mkdir()

    with open("../../var/bnd-repo/repos/index.json", "w") as f:
        f.write("{}")

if not os.path.exists("../../var/bnd-repo/config.json"):
    with open("../../var/bnd-repo/config.json", "w") as f:
        f.write("{}")

