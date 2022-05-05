"""Code for downloading and retrieving modules from standard library"""

from json.decoder import JSONDecodeError
import os
import re
import bs4
import wget
import requests
import logging
import jsonpickle
import subprocess
import py4a.api.dynamic as dynamic

from typing import Dict, List
from py4a.api.entity import Package
from py4a.api.static import get_apis_from_dir, get_apis_from_file
from py4a.api.dynamic import _list_conda_envs, _remove_env, _create_env


logger = logging.getLogger(__name__)
PATH = "data/python"


def download_python_source(path: str = PATH):
    """Downloads all Python source releases"""
    os.makedirs(path, exist_ok=True)

    py_vers = re.findall(
        r"href=\"(\d+\.\d+\.\d+)/\"",
        requests.get("https://www.python.org/ftp/python/").text,
    )

    for ver in py_vers:
        logger.info(f"Downloading Python {ver}")
        outfile = os.path.join(path, f"Python-{ver}.tgz")
        if os.path.exists(outfile):
            continue
        try:
            wget.download(
                f"https://www.python.org/ftp/python/{ver}/Python-{ver}.tgz",
                out=outfile,
            )
        except Exception as ex:
            logger.error(f"Error while downloading Python {ver}: {ex}")
            continue


def extract_stdlib_apis_static(path: str = PATH) -> Dict[str, Package]:
    """Extracts Python standard lib APIs from source releases using static analysis"""
    for py_file in os.listdir(path):
        if not py_file.endswith(".tgz"):
            continue
        if py_file.startswith("Python-2"):
            logger.info(
                f"Skipping {py_file} because currently Python 2.x is not supported"
            )
            continue

        ver = re.search(r"Python-(\d+\.\d+\.\d+)", py_file).group(1)
        apis = {}

        logger.info(f"Extracting Python {ver}: {py_file}")
        try:
            os.system(f"tar -xzf {os.path.join(path, py_file)} -C {path}")
        except Exception as ex:
            logger.error(f"Error while extracting {py_file}: {ex}")
            continue

        logger.info(f"Extracting APIs for {py_file}")
        lib_path = os.path.join(path, py_file.replace(".tgz", ""), "Lib")
        for filename in os.listdir(lib_path):
            if filename == "test":
                continue
            pkg_path = os.path.join(lib_path, filename)
            if pkg_path.endswith(".py"):
                pkg_name = filename.replace(".py", "")
                pkg = get_apis_from_file(pkg_name, pkg_path)
                apis[pkg_name] = pkg
            elif os.path.isdir(pkg_path):
                pkg = get_apis_from_dir(filename, pkg_path)
                apis[filename] = pkg
        logger.info(f"Python {ver}: {len(apis)} stdlib APIs")
        logger.info(f"Python {ver}: top levels = {list(apis.keys())}")

        with open(os.path.join(path, f"{ver}-static.json"), "w") as f:
            f.write(jsonpickle.encode(apis))


def extract_stdlib_apis_dynamic(path: str = PATH) -> Dict[str, Package]:
    """Extract Python standard APIs for Python >= 3.6 using dynamic analysis"""
    for py_file in os.listdir(path):
        if not py_file.endswith(".tgz"):
            continue

        ver = re.search(r"Python-(\d+\.\d+\.\d+)", py_file).group(1)
        major, minor, patch = ver.split(".")
        if int(major) != 3 or int(minor) <= 6:
            logger.info(f"Skipping Python {ver} because it is not supported")
            continue

        top_levels = []
        soup = bs4.BeautifulSoup(
            requests.get(
                f"https://docs.python.org/{major}.{minor}/py-modindex.html"
            ).text,
            "html.parser",
        )
        for link in soup.find_all("a"):
            if link.get("href").startswith("library/"):
                top_level = link.find("code").text
                if "." not in top_level:
                    top_levels.append(top_level)

        conda_env = "Python-" + ver
        if conda_env in _list_conda_envs():
            _remove_env(conda_env)
        if not _create_env(conda_env, ver):
            logger.info(f"Cannot create conda environment for Python {ver}")
            continue

        logger.info(f"Extracting APIs for {ver}")
        apis = {}
        for top_level in top_levels:
            logger.info(f"  {top_level}")
            try:
                result = subprocess.run(
                    [
                        "conda",
                        "run",
                        "-n",
                        conda_env,
                        "python",
                        "-m",
                        dynamic.__name__,
                        top_level,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                apis[top_level] = jsonpickle.decode(result.stdout.decode("utf-8"))
            except JSONDecodeError:
                logger.error(f"Error while extracting APIs for {top_level}")

        logger.info(f"Python {ver}: {len(apis)} stdlib APIs")
        logger.info(f"Python {ver}: top levels = {list(apis.keys())}")

        with open(os.path.join(path, f"{ver}-dynamic.json"), "w") as f:
            f.write(jsonpickle.encode(apis))
        _remove_env(conda_env)


def get_python_versions(path: str = PATH, dynamic: bool = False) -> List[str]:
    """Returns a list of Python versions with APIs available"""
    if dynamic:
        return [
            f.replace("-dynamic.json", "")
            for f in os.listdir(path)
            if f.endswith("-dynamic.json")
        ]
    else:
        return [
            f.replace("-static.json", "")
            for f in os.listdir(path)
            if f.endswith("-static.json")
        ]


def get_stdlib_apis(
    ver: str, path: str = PATH, dynamic: bool = False
) -> Dict[str, Package]:
    """Returns a dictionary of all Python standard library APIs"""
    if dynamic:
        with open(os.path.join(path, f"{ver}-dynamic.json"), "r") as f:
            return jsonpickle.decode(f.read())
    else:
        with open(os.path.join(path, f"{ver}-static.json"), "r") as f:
            return jsonpickle.decode(f.read())


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    download_python_source()
    extract_stdlib_apis_static()
    extract_stdlib_apis_dynamic()
    logger.info(f"Done!")
