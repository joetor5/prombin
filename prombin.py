# Copyright (c) 2024 Joel Torres
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://opensource.org/license/mit.

import sys
import os
import subprocess
import signal
import argparse
import requests
import json
import platform
import hashlib
import shutil
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup

__version__ = "1.1"

PROM_URL = "https://prometheus.io/download/"
PROM_PROC = "prometheus"
PROM_HOME = Path.joinpath(Path.home(), PROM_PROC)
PROM_BIN = Path.joinpath(PROM_HOME, PROM_PROC)
PROM_TOOL_BIN = Path.joinpath(PROM_HOME, "promtool")
PROM_CONFIG = Path.joinpath(PROM_HOME, "prometheus.yml")
PROM_VERSION_JSON = Path.joinpath(PROM_HOME, ".version")
PROM_TMP = Path.joinpath(PROM_HOME, "tmp")

DOWNLOAD_CHUNK_SIZE = 10 * 1024
HASH_READ_CHUNK_SIZE = 65536

ERROR_FETCH = 1
ERROR_CHECKSUM = 2
ERROR_HTML_PARSE = 3
ERROR_PROM_NOT_INSTALLED = 4
ERROR_CMD_ARG = 5


def get_os_details():
    name = platform.system().lower()
    arch = platform.machine().lower()
    details = {
        "name": name,
        "arch": arch
    }

    if arch == "x86_64":
        details["arch"] = "amd64"
    elif arch == "aarch64":
        details["arch"] = "arm64"

    return details

def get_process_id(name=PROM_PROC):
    try:
        return int(subprocess.check_output(["pgrep", name]))
    except subprocess.CalledProcessError:
        return 0

def stop_process(name=PROM_PROC):
    pid = get_process_id(name)
    if pid:
        os.kill(pid, signal.SIGTERM)

def fetch(url, stream=False):
    response = requests.get(url, stream=stream)
    if response.ok:
        return response
    else:
        print("error: unable to fetch[{}]: {}".format(response.status_code, url))
        sys.exit(ERROR_FETCH)

def get_download_details(lts=False):
    os_details = get_os_details()
    page_doc = BeautifulSoup(fetch(PROM_URL).text, "html.parser")
    
    table_index = 0 if not lts else 1
    try:
        table = page_doc.find_all("table")[0] # prometheus table

        section_version = table.find_all("thead")[table_index]
        version = section_version.find_all("tr")[0].find("td").get_text()

        section_files = table.find_all("tbody")[table_index]
        download_row = section_files.find("tr", {"data-os": os_details["name"], "data-arch": os_details["arch"]})
        filename_data = download_row.find("td", class_="filename")

        download_details = {
            "version": version.split("/")[0].strip(),
            "url": filename_data.find("a").attrs["href"],
            "filename": filename_data.get_text(),
            "checksum": download_row.find("td", class_="checksum").get_text()
        }
    except (AttributeError, IndexError) as e:
        print("error: {}".format(e))
        sys.exit(ERROR_HTML_PARSE)

    return download_details


def download(lts=False, download_details=None, download_dir=PROM_TMP):
    if not download_dir.exists():
        download_dir.mkdir()
    
    if not download_details:
        details = get_download_details(lts)
    else:
        details = download_details
    
    filename = details["filename"]
    details["file_path"] = Path.joinpath(download_dir, filename)

    response = fetch(details["url"], stream=True)
    file_size = int(response.headers.get("Content-Length", 0))

    print("Downloading {}...".format(filename))
    with tqdm(total=file_size, unit="B", unit_scale=True, colour="GREEN") as download_bar:
        with open(details["file_path"], mode="wb") as f:
            for chunk in tqdm(response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE)):
                download_bar.update(len(chunk))
                f.write(chunk)

    return details

def compute_hash_checksum(download_details):
    file_name = download_details["file_path"]
    checksum = download_details["checksum"]

    sha256 = hashlib.sha256()
    with open(file_name, mode="rb") as f:
        while True:
            data = f.read(HASH_READ_CHUNK_SIZE)
            if not data:
                break
            sha256.update(data)
    
    print("Validating checksum... ", end="")
    digest = sha256.hexdigest()
    if digest != checksum:
        print("error: checksum didn't match")
        sys.exit(ERROR_CHECKSUM)
    print("OK")

    return digest

def extract_and_copy_files(download_details, extract_dir=PROM_TMP, install_dir=PROM_HOME, new_install=False):
    filename = download_details["filename"]
    copy_from = filename.replace(".tar.gz", "")
    copy_from = copy_from.replace(".zip", "")

    print("Unpacking {}... ".format(filename), end="")
    shutil.unpack_archive(download_details["file_path"], extract_dir=extract_dir,
                          format="gztar", filter="data")
    print("OK")
    
    files = ["prometheus", "promtool"]
    if new_install:
        files.append("prometheus.yml")

    print("Installing files to {}... ".format(PROM_HOME), end="")
    for file in files:
        file_path = Path.joinpath(extract_dir, copy_from, file)
        shutil.copy(file_path, install_dir)
    print("OK")

def is_prom_installed():
    return PROM_HOME.exists() and PROM_BIN.exists() and PROM_TOOL_BIN.exists() and PROM_CONFIG.exists() and PROM_VERSION_JSON.exists()

def save_version_details(version, file_path=PROM_VERSION_JSON, lts=False):
    details = {"version": version, "lts": lts}

    with open(file_path, "w") as f:
        f.write(json.dumps(details))

def load_version_details(file_path=PROM_VERSION_JSON):
    with open(file_path) as f:
        return json.loads(f.read())

def install(args):
    if is_prom_installed():
        print("Prometheus already installed. Run with the command 'update' for the latest version.")
        sys.exit(0)

    if not PROM_HOME.exists():
        PROM_HOME.mkdir()
    
    download_details = download(lts=args.lts)
    compute_hash_checksum(download_details)
    extract_and_copy_files(download_details, new_install=True)
    save_version_details(download_details["version"], lts=args.lts)

def update(args):
    if not is_prom_installed():
        print("Prometheus not installed. Run with the command 'install' to install.")
        sys.exit(ERROR_PROM_NOT_INSTALLED)
    
    version_details = load_version_details()
    lts = version_details["lts"]
    download_details = get_download_details(lts=lts)
    installed_version = version_details["version"]
    latest_version = download_details["version"]

    if args.check:
        print("Latest version: {}".format(latest_version))
        print("Installed version: {}".format(installed_version))
        sys.exit(0)
    
    if installed_version == latest_version:
        print("Installed Prometheus is on the latest version, nothing to update.")
        sys.exit(0)

    download_details = download(lts=lts, download_details=download_details)
    compute_hash_checksum(download_details)
    print("Stopping {} before copying files... ".format(PROM_PROC), end="")
    stop_process()
    print("OK")
    extract_and_copy_files(download_details)
    save_version_details(latest_version, lts=lts)

def main():
    parser = argparse.ArgumentParser(prog="prombin")
    parser.add_argument("-v", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(title="commands")
    
    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("-s", "--lts", action="store_true", help="LTS version")
    install_parser.set_defaults(func=install)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("-c", "--check", action="store_true", help="Check latest version")
    update_parser.set_defaults(func=update)


    args = parser.parse_args()
    try:
        args.func(args)
    except AttributeError as e:
        print("Error running command: {}: {}".format(args, e))
        sys.exit(ERROR_CMD_ARG)
    

if __name__ == "__main__":
    main()
