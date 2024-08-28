# Copyright (c) 2024 Joel Torres
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://opensource.org/license/mit.

from prombin import *
import os
import re
import tarfile

ROOT_DIR = Path.cwd()
TEST_DIR = Path.joinpath(ROOT_DIR, "tmp")
TEST_DOWNLOAD_TMP = Path.joinpath(TEST_DIR, "archives")
TEST_VERSION = "2.54.0"
TEST_VERSIONS = (("2.54.0", False), ("2.53.2", True))
TEST_BIN = Path.joinpath(TEST_DIR, "prometheus")
TEST_TOOL_BIN = Path.joinpath(TEST_DIR, "promtool")
TEST_CONFIG = Path.joinpath(TEST_DIR, "prometheus.yml")
TEST_VERSION_JSON = Path.joinpath(TEST_DIR, "test.json")
TEST_DOWNLOAD_URL = "https://github.com/prometheus/prometheus/releases/download/v2.54.0/prometheus-2.54.0.darwin-arm64.tar.gz"
TEST_CHECKSUM = "5fe1f91cb1b8f69c56981f5ae0109a61ef787f0b70b7bc862bb1fd343d75b056"
TEST_ARCHIVE_DIR = "prometheus-2.54.0.darwin-arm64"
TEST_ARCHIVE_FILES = [TEST_BIN, TEST_TOOL_BIN, TEST_CONFIG]
TEST_TAR_FILE = "{}.tar.gz".format(TEST_ARCHIVE_DIR)
TEST_TAR_FILE_PATH = Path.joinpath(TEST_DOWNLOAD_TMP, TEST_TAR_FILE)
TEST_ZIP_FILE = "{}.zip".format(TEST_ARCHIVE_DIR)
TEST_PROC = "sleep"
TEST_PROC_ARGS = "300 &"

OS_NAME = "darwin"
OS_ARCH = "arm64"

if not TEST_DIR.exists():
    TEST_DIR.mkdir()

if not TEST_DOWNLOAD_TMP.exists():
    TEST_DOWNLOAD_TMP.mkdir()


def test_get_os_details():
    details = get_os_details()
    assert details["name"] == OS_NAME
    assert details["arch"] == OS_ARCH

def test_get_process_id():
    subprocess.run(["bash", "-c", "{} {}".format(TEST_PROC, TEST_PROC_ARGS)])
    assert get_process_id(name=TEST_PROC) != 0

def test_stop_process():
    stop_process(name=TEST_PROC)
    assert get_process_id(name=TEST_PROC) == 0

def test_fetch():
    resp = fetch(PROM_URL)
    assert resp.status_code == 200
    assert len(resp.text) != 0

    resp = fetch(TEST_DOWNLOAD_URL, stream=True)
    assert resp.status_code == 200

def test_get_download_details():
    details = get_download_details()
    version_pattern = "[0-9]+\\.[0-9]+\\.[0-9]+"
    file_pattern = "prometheus-{}.+[zipgz]$".format(version_pattern)
    url_pattern = "https://github.+{}".format(file_pattern)

    assert re.search(version_pattern, details["version"])
    assert re.search(url_pattern, details["url"])
    assert re.search(file_pattern, details["filename"])
    assert len(details["checksum"]) == 64

def test_compute_hash_checksum():
    details = {
        "file_path": "LICENSE",
        "checksum": TEST_CHECKSUM
    }

    assert compute_hash_checksum(details) == TEST_CHECKSUM

def test_extract_and_copy_files():
    details = {
        "filename": TEST_TAR_FILE,
        "file_path": TEST_TAR_FILE_PATH
    }
    generate_archive()

    extract_and_copy_files(details, extract_dir=TEST_DOWNLOAD_TMP, install_dir=TEST_DIR, new_install=False)
    assert TEST_BIN.exists()
    assert TEST_TOOL_BIN.exists()
    assert not TEST_CONFIG.exists()

    extract_and_copy_files(details, extract_dir=TEST_DOWNLOAD_TMP, install_dir=TEST_DIR, new_install=True)
    for file in TEST_ARCHIVE_FILES:
        assert file.exists()
    
    shutil.rmtree(TEST_DOWNLOAD_TMP)


def test_save_load_version_details():
    for version, is_lts in TEST_VERSIONS:
        save_version_details(version=version, file_path=TEST_VERSION_JSON, lts=is_lts)
        assert TEST_VERSION_JSON.exists()
        version_details = load_version_details(file_path=TEST_VERSION_JSON)
        assert version_details["version"] == version
        assert version_details["lts"] == is_lts
        TEST_VERSION_JSON.unlink()


def test_download():
    details = {
        "filename": TEST_TAR_FILE,
        "url": TEST_DOWNLOAD_URL
    }
    download(download_details=details, download_dir=TEST_DOWNLOAD_TMP)

    assert TEST_TAR_FILE_PATH.exists()

def generate_archive():
    archive_dir = Path.joinpath(TEST_DOWNLOAD_TMP, TEST_ARCHIVE_DIR)
    if not archive_dir.exists():
        archive_dir.mkdir()
    
    for file in TEST_ARCHIVE_FILES:
        file.touch()
        shutil.copy(file, archive_dir)
        file.unlink()
    
    os.chdir(TEST_DOWNLOAD_TMP)
    with tarfile.open(TEST_TAR_FILE, "w:gz") as tar:
        tar.add(TEST_ARCHIVE_DIR)

    shutil.rmtree(archive_dir)
    os.chdir(ROOT_DIR)
