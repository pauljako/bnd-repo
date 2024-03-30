#!/bin/python3
import json
import os
import sys
import time
from urllib.request import urlretrieve
import boundaries


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


QUOTE_SYMBOL_DOING = f" {Colors.BOLD}{Colors.OKCYAN}::{Colors.ENDC} "
QUOTE_SYMBOL_WARNING = f" {Colors.BOLD}{Colors.WARNING}::{Colors.ENDC} "
QUOTE_SYMBOL_INFO = f" {Colors.BOLD}{Colors.OKGREEN}::{Colors.ENDC} "
QUOTE_SYMBOL_ERROR = f" {Colors.BOLD}{Colors.FAIL}::{Colors.ENDC} "
QUOTE_SYMBOL_OUTPUT = f" {Colors.BOLD}{Colors.OKBLUE}::{Colors.ENDC} "

VAR_DIR = os.path.realpath(os.path.expanduser(os.environ.get("VAR_DIR", "~/boundaries/var/bnd-repo")))

os.chdir(os.path.join(VAR_DIR, "tmp"))

REPO_PATH = os.path.realpath(os.path.expanduser(os.path.join(VAR_DIR, "repos")))
REPO_INDEX_FILE = os.path.realpath(os.path.join(REPO_PATH, "index.json"))
CONFIG_PATH = os.path.realpath(os.path.expanduser(os.path.join(VAR_DIR, "config.json")))

cur_chunk: int
total_chunks: int
do_not_give_output: bool
config = {"silent": False}


def load_config():
    global config, CONFIG_PATH
    with open(CONFIG_PATH, "rb") as f:
        config = json.load(f)
    if "silent" not in config:
        config["silent"] = False


load_config()


def report_hook(block_count, block_size, file_size):
    global cur_chunk, total_chunks, do_not_give_output
    downloaded = block_count * block_size
    percentage = round(downloaded / file_size * 100)
    if percentage > 100:
        percentage = 100
    downloaded = round(downloaded / 1000000, 1)
    size = round(file_size / 1000000, 1)
    if downloaded > size:
        downloaded = size
    if not do_not_give_output:
        print(
            f"{QUOTE_SYMBOL_DOING}Downloading Chunk {cur_chunk}/{total_chunks}: {downloaded}MB/{size}MB ({percentage}%){QUOTE_SYMBOL_DOING}",
            end="     \r")


def getrepos() -> dict | None:
    if os.path.exists(REPO_INDEX_FILE):
        with open(REPO_INDEX_FILE, "rb") as f:
            repo_index = json.load(f)
    else:
        print(f"{QUOTE_SYMBOL_ERROR}No Repository Index File Found{QUOTE_SYMBOL_ERROR}")
        return None
    return repo_index


def update_index_files(silent: bool = False):
    repos = getrepos()

    for r, u in repos.items():
        repo_file_path = os.path.realpath(os.path.join(REPO_PATH, r + ".json"))
        if os.path.exists(repo_file_path):
            cached = True
        else:
            cached = False
        if not silent: print(f"{QUOTE_SYMBOL_DOING}Updating {r} Repository{QUOTE_SYMBOL_DOING}")
        time.sleep(0.2)
        urlretrieve(f"{u}/index.json", "temp.json")
        time.sleep(0.2)
        with open("temp.json", "rt") as f:
            rf = f.read()
        if rf.startswith("{"):
            if cached:
                os.remove(repo_file_path)
            os.rename("temp.json", repo_file_path)
            number_of_packages = len(json.loads(rf))
            if not silent: print(
                f"{QUOTE_SYMBOL_INFO}Updated {r} Repository. {number_of_packages} Packages available{QUOTE_SYMBOL_INFO}")
        else:
            if cached:
                if not silent: print(
                    f"{QUOTE_SYMBOL_WARNING}Could not Update {r} Repository, using cached{QUOTE_SYMBOL_WARNING}")
            else:
                if not silent: print(f"{QUOTE_SYMBOL_ERROR}Could not Update {r} Repository{QUOTE_SYMBOL_ERROR}")
                with open(repo_file_path, "w") as f:
                    f.write("{}")
            os.remove("temp.json")


def loadrepo(repo_name) -> dict | None:
    repo_path = os.path.join(REPO_PATH, repo_name + ".json")
    if not os.path.exists(repo_path):
        return None
    with open(repo_path, "rb") as f:
        repo = json.load(f)
    return repo


def search(name: str, silent: bool = False) -> dict:
    found = {}
    repos = getrepos()
    if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}Results for {name}:")
    for repo in repos.keys():
        index = loadrepo(repo)
        for pkg in index.keys():
            if name == pkg or pkg.startswith(name) or pkg.endswith(name):
                found[pkg] = repo
                if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}{pkg} ({repo})")
    return found


def list_all(silent: bool = False) -> dict:
    pkgs = {}
    repos = getrepos()
    if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}List of all available packages:")
    for repo in repos.keys():
        index = loadrepo(repo)
        for pkg in index.keys():
            pkgs[pkg] = repo
            if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}{pkg} ({repo})")
    return pkgs


def get(name, silent: bool = False) -> str | None:
    global cur_chunk, total_chunks, do_not_give_output
    if not silent: print(f"{QUOTE_SYMBOL_DOING}Searching for {name} in{QUOTE_SYMBOL_DOING}")
    repos = getrepos()
    selected_repo = None
    for r in repos.keys():
        if not silent: print(f"{QUOTE_SYMBOL_DOING}{r}{QUOTE_SYMBOL_DOING}", end="\r")
        repo = loadrepo(r)
        if name in repo:
            if not silent: print(f"{QUOTE_SYMBOL_INFO}{r} - Found{QUOTE_SYMBOL_INFO}", end="\r")
            selected_repo = r
            break
        else:
            if not silent: print(f"{QUOTE_SYMBOL_ERROR}{r} - Not Found{QUOTE_SYMBOL_ERROR}", end="\r")
    if selected_repo is None:
        if not silent: print(f"\n{QUOTE_SYMBOL_ERROR}{name} could not be found{QUOTE_SYMBOL_ERROR}")
        return None
    if not silent: print(f"\n{QUOTE_SYMBOL_DOING}Downloading {name} from {selected_repo}{QUOTE_SYMBOL_DOING}", end="")
    time.sleep(0.2)
    repo = loadrepo(selected_repo)
    server_filepath: str = repo[name]
    filename = server_filepath.split("/")[-1] + ".tar.gz"
    if os.path.exists(filename):
        os.remove(filename)
    urlretrieve(f"{os.path.join(repos[selected_repo], server_filepath)}/index.json", "index.json")
    with open("index.json", "rt") as f:
        chunks = json.loads(f.read())
    cur_chunk = 1
    total_chunks = len(chunks)
    do_not_give_output = silent
    if not silent: print("")
    for p in chunks:
        urlretrieve(f"{os.path.join(repos[selected_repo], server_filepath)}/{p}", "tmp", reporthook=report_hook)
        os.system(f"cat tmp >> {filename}")
        os.remove("tmp")
        cur_chunk += 1
    if not silent: print("")
    return filename


if __name__ == '__main__':
    muted = config["silent"]
    try:
        action = sys.argv[1]
    except IndexError:
        print(f"{QUOTE_SYMBOL_ERROR}No Argument given{QUOTE_SYMBOL_ERROR}")
        action = ""
    if action == "install":
        dl_pkg = get(sys.argv[2], muted)
        if dl_pkg is None:
            if input(f"{QUOTE_SYMBOL_ERROR}Download Error. Do you want to Update the Repositories? (Y/n) ") != "n":
                update_index_files()
                dl_pkg = get(sys.argv[2])
                if dl_pkg is None:
                    print(f"{QUOTE_SYMBOL_ERROR}Download Error.{QUOTE_SYMBOL_ERROR}")
                    exit()
            else:
                exit()
        if boundaries.install(dl_pkg):
            print(f"{QUOTE_SYMBOL_INFO}{sys.argv[2]} was installed successfully{QUOTE_SYMBOL_INFO}")
        else:
            print(f"{QUOTE_SYMBOL_ERROR}{sys.argv[2]} was not installed successfully{QUOTE_SYMBOL_ERROR}")
        if os.path.exists(dl_pkg): os.remove(dl_pkg)
    elif action == "update":
        update_index_files(muted)
    elif action == "search":
        search(sys.argv[2])
    elif action == "list":
        list_all()
    else:
        print(f"{QUOTE_SYMBOL_ERROR}Unknown Command \"{action}\"{QUOTE_SYMBOL_ERROR}")
