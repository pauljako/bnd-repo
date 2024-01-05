#!/bin/python3
import json
import os
import sys
import time

import boundaries

REPO_PATH = os.path.realpath("repos")
REPO_INDEX_FILE = os.path.realpath(os.path.join(REPO_PATH, "index.json"))


def getrepos() -> dict | None:
    if os.path.exists(REPO_INDEX_FILE):
        with open(REPO_INDEX_FILE, "rb") as f:
            repo_index = json.load(f)
    else:
        print("Error. No Repository Index File Found.")
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
        if not silent: print(f"Updating {r} Repository")
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
                if not silent: print(f"Warning: Could not Update {r} Repository, using cached")
            else:
                if not silent: print(f"Error: Could not Update {r} Repository")
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


def get(name, silent: bool = False) -> str | None:
    if not silent: print(f"Searching for {name} in")
    repos = getrepos()
    selected_repo = None
    for r in repos.keys():
        if not silent: print(f"{r}", end="\r")
        repo = loadrepo(r)
        if name in repo:
            if not silent: print(f"{r} - Found", end="\r")
            selected_repo = r
            break
        else:
            if not silent: print(f"{r} - Not Found", end="\r")
    if selected_repo is None:
        if not silent: print(f"\n{name} could not be found")
        return None
    if not silent: print(f"\nDownloading {name} from {selected_repo}")
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
        print("Error: No Argument given")
        action = ""
    if action == "install":
        dl_pkg = get(sys.argv[2])
        if dl_pkg is None:
            if input("Download Error. Do you want to Update the Repository? (Y/n) ") != n:
                update_index_files()
                dl_pkg = get(sys.argv[2])
                if dl_pkg is None:
                    print("Download Error.")
                    exit()
            else:
                exit()
        if boundaries.install(dl_pkg):
            print(f"{sys.argv[2]} was installed successfully")
        else:
            print(f"{sys.argv[2]} was not installed successfully")
        if os.path.exists(dl_pkg): os.remove(dl_pkg)
    elif action == "update":
        update_index_files()
    elif action == "search":
        search()
    else:
        print(f"Error: Invalid Command \"{action}\"")
