#!/usr/bin/env python3
import argparse
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

def setrepos(repo: dict):
    with open(file=REPO_INDEX_FILE, mode="wt") as f:
        json.dump(obj=repo, fp=f)

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


def search(name: str, silent: bool = False, exact: bool = False, from_repo: str = None) -> dict:
    found = {}
    if from_repo is not None:
        if from_repo in getrepos():
            repos = {from_repo: getrepos()[from_repo]}
        else:
            if not silent: print(f"{QUOTE_SYMBOL_ERROR}Repo {from_repo} not found{QUOTE_SYMBOL_ERROR}")
            return {}
    else:
        repos = getrepos()
    if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}Results for {name}:")
    for repo in repos.keys():
        index = loadrepo(repo)
        for pkg in index.keys():
            if not exact:
                if name == pkg or pkg.startswith(name) or pkg.endswith(name):
                    found[pkg] = repo
                    if "version" in index[pkg]:
                        version = f", Version: {index[pkg]['version']}"
                    else:
                        version = ""
                    if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}{pkg} (Repository: {repo}{version})")
            else:
                if name == pkg:
                    found[pkg] = repo
                    if "version" in index[pkg]:
                        version = f", Version: {index[pkg]['version']}"
                    else:
                        version = ""
                    if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}{pkg} (Repository: {repo}{version})")
    return found


def list_all(silent: bool = False, from_repo: str = None) -> dict:
    pkgs = {}
    if from_repo is not None:
        if from_repo in getrepos():
            repos = {from_repo: getrepos()[from_repo]}
        else:
            if not silent: print(f"{QUOTE_SYMBOL_ERROR}Repo {from_repo} not found{QUOTE_SYMBOL_ERROR}")
            return
    else:
        repos = getrepos()
    if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}List of all available packages:")
    for repo in repos.keys():
        index = loadrepo(repo)
        for pkg in index.keys():
            pkgs[pkg] = repo
            if "version" in index[pkg]:
                version = f", Version: {index[pkg]['version']}"
            else:
                version = ""
            if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}{pkg} (Repository: {repo}{version})")
    return pkgs

def add_repo(name: str, url: str):
    repo = getrepos()
    repo[name] = url
    setrepos(repo)
    
def remove_repo(name: str):
    repo = getrepos()
    repo.pop(name)
    setrepos(repo)

def get(name, silent: bool = False, from_repo: str = None) -> str | None:
    global cur_chunk, total_chunks, do_not_give_output
    if not silent: print(f"{QUOTE_SYMBOL_DOING}Searching for {name} in{QUOTE_SYMBOL_DOING}")
    if from_repo is not None:
        if from_repo in getrepos():
            repos = {from_repo: getrepos()[from_repo]}
        else:
            if not silent: print(f"{QUOTE_SYMBOL_ERROR}Repo {from_repo} not found{QUOTE_SYMBOL_ERROR}")
            return None
    else:
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
    obj_in_repo = repo[name]
    server_filepath: str = obj_in_repo["url"]
    if "suffix" in obj_in_repo:
        suffix = obj_in_repo["suffix"]
    else:
        suffix = "tar.gz"
    filename = server_filepath.split("/")[-1] + "." + suffix
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


def get_outdated_packages(silent: bool = False, from_repo: str = None) -> list:
    outdated_pkgs = []
    pkgs = boundaries.get_packages()
    if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}List of outdated Packages:")
    for pkg in pkgs:
        info = boundaries.getpkginfo(packagename=pkg)
        if info is not None and ("version" in info):
            result = search(name=pkg, silent=True, exact=True, from_repo=from_repo)
            if pkg in result:
                contained_repo = loadrepo(repo_name=result[pkg])
                if pkg in contained_repo:
                    pkg_in_repo = contained_repo[pkg]
                    if "version" in pkg_in_repo:
                        if pkg_in_repo["version"] != info["version"]:
                            if not silent: print(f"{QUOTE_SYMBOL_OUTPUT}{pkg} (Installed: {info['version']}, Available: {pkg_in_repo['version']})")
                            outdated_pkgs.append(pkg)
    return outdated_pkgs


def install(pkg, silent: bool = False, from_repo: str = None) -> bool:
    dl_pkg = get(pkg, silent, from_repo=from_repo)
    if dl_pkg is None:
        if not silent: print(f"{QUOTE_SYMBOL_ERROR}Download Error. Please update your Repositories{QUOTE_SYMBOL_ERROR}")
        return False
    result = boundaries.install(dl_pkg)
    if os.path.exists(dl_pkg):
        os.remove(dl_pkg)
    if result:
        if not silent: print(f"{QUOTE_SYMBOL_INFO}{pkg} was installed successfully{QUOTE_SYMBOL_INFO}")
        return True
    else:
        if not silent: print(f"{QUOTE_SYMBOL_ERROR}{pkg} was not installed successfully{QUOTE_SYMBOL_ERROR}")
        return False


def upgrade_outdated(silent: bool = False):
    outdated = get_outdated_packages(silent)
    if not silent: print(f"{QUOTE_SYMBOL_WARNING}Installing in 3 Seconds{QUOTE_SYMBOL_WARNING}")
    time.sleep(3)
    for i in outdated:
        install(i, silent)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="bnd", description="The boundaries Repository Manager")
    
    subcommand = parser.add_subparsers(title="Actions", dest="action")
    
    install_parser = subcommand.add_parser(name="install", help="Install a Package")
    install_parser.add_argument("--force-repo", help="Force the use of a specific Repository", default=None, dest="fromrepo")
    install_parser.add_argument("package", help="The Package to install")
    
    update_parser = subcommand.add_parser(name="update", help="Update the Repositories")
    
    search_parser = subcommand.add_parser(name="search", help="Search for Packages")
    search_parser.add_argument("--force-repo", help="Force the use of a specific Repository", default=None, dest="fromrepo")
    search_parser.add_argument("term", help="The Search Term")
    
    list_parser = subcommand.add_parser(name="list", help="List available Packages")
    list_parser.add_argument("--force-repo", help="Force the use of a specific Repository", default=None, dest="fromrepo")
    list_parser.add_argument("--outdated", action="store_true", help="Only List outdated Packages")
    
    upgrade_parser = subcommand.add_parser(name="upgrade", help="Upgrade outdated Packages")
    
    repo_parser = subcommand.add_parser(name="repo", help="Manage Repositories")
    
    repo_subcommand = repo_parser.add_subparsers(title="Actions", dest="repo_action")
    
    add_repo_parser = repo_subcommand.add_parser(name="add", help="Add a Repository")
    add_repo_parser.add_argument("name", help="The Name of the Repository")
    add_repo_parser.add_argument("url", help="The Path/Url to the Repository")
    
    remove_repo_parser = repo_subcommand.add_parser(name="remove", help="Remove a Repository")
    remove_repo_parser.add_argument("name", help="The name of the Repository to remove")
    
    args = parser.parse_args()
    
    muted = config["silent"]
    
    if args.action == "install":
        install(pkg=args.package, from_repo=args.fromrepo)
    elif args.action == "update":
        update_index_files(silent=muted)
    elif args.action == "search":
        search(name=args.term, from_repo=args.fromrepo)
    elif args.action == "list" and not args.outdated:
        list_all(from_repo=args.fromrepo)
    elif args.action == "list" and args.outdated:
        get_outdated_packages(from_repo=args.fromrepo)
    elif args.action == "upgrade":
        upgrade_outdated(silent=muted)
    elif args.action == "repo":
        if args.repo_action == "add":
            add_repo(name=args.name, url=args.url)
            update_index_files(silent=muted)
        elif args.repo_action == "remove":
            remove_repo(name=args.name)
            update_index_files(silent=muted)
