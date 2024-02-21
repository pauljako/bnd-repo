#!/bin/python3
import json
import os
import sys
import time

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


QUOTE_SYMBOL_DOING = f"{Colors.BOLD}{Colors.OKCYAN}::{Colors.ENDC}"
QUOTE_SYMBOL_WARNING = f"{Colors.BOLD}{Colors.WARNING}::{Colors.ENDC}"
QUOTE_SYMBOL_INFO = f"{Colors.BOLD}{Colors.OKGREEN}::{Colors.ENDC}"
QUOTE_SYMBOL_ERROR = f"{Colors.BOLD}{Colors.FAIL}::{Colors.ENDC}"

os.chdir(os.path.realpath(os.path.expanduser(os.environ.get("APP_DIR", "~/boundaries/apps/bnd-repo"))))

REPO_PATH = os.path.realpath(os.path.expanduser(os.path.join(os.environ.get("VAR_DIR", "~/boundaries/var/bnd-repo"), "repos")))
REPO_INDEX_FILE = os.path.realpath(os.path.join(REPO_PATH, "index.json"))


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
        os.system(f"curl {u}/index.json > temp.json")
        time.sleep(0.2)
        with open("temp.json", "rt") as f:
            rf = f.read()
        if rf.startswith("{"):
            if cached:
                os.remove(repo_file_path)
            os.rename("temp.json", repo_file_path)
        else:
            if cached:
                if not silent: print(f"{QUOTE_SYMBOL_WARNING}Could not Update {r} Repository, using cached{QUOTE_SYMBOL_WARNING}")
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


def search(name: str, silent=False) -> dict:
    found = {}
    repos = getrepos()
    for repo in repos.keys():
        index = loadrepo(repo)
        for pkg in index.keys():
            if name == pkg or pkg.startswith(name) or pkg.endswith(name):
                found[pkg] = repo
                if not silent: print(f"{QUOTE_SYMBOL_INFO}{pkg} ({repo})")
    return found


def get(name, silent: bool = False) -> str | None:
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
    if not silent: print(f"\n{QUOTE_SYMBOL_DOING}Downloading {name} from {selected_repo}{QUOTE_SYMBOL_DOING}")
    time.sleep(0.2)
    repo = loadrepo(selected_repo)
    server_filepath: str = repo[name]
    filename = server_filepath.split("/")[-1]
    print(filename)
    dls = os.system(f"curl {os.path.join(repos[selected_repo], server_filepath)} > {filename}")
    return filename


if __name__ == '__main__':
    try:
        action = sys.argv[1]
    except:
        print(f"{QUOTE_SYMBOL_ERROR}No Argument given{QUOTE_SYMBOL_ERROR}")
        action = ""
    if action == "install":
        dl_pkg = get(sys.argv[2])
        if dl_pkg is None:
            if input(f"{QUOTE_SYMBOL_ERROR}Download Error. Do you want to Update the Repository? (Y/n) ") != "n":
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
        update_index_files()
    elif action == "search":
        search(sys.argv[2])
    else:
        print(f"{QUOTE_SYMBOL_ERROR}Invalid Command \"{action}\"{QUOTE_SYMBOL_ERROR}")
