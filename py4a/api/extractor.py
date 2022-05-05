"""Utilities for downloading Python packages, release notes, and extracting APIs"""

import os
import json
import time
import wget
import requests
import argparse
import logging
import pathlib
import traceback
import zipfile
import jsonpickle
import multiprocessing as mp
import py4a.api.static as static
import py4a.api.entity as entity

from copy import deepcopy
from typing import Dict, List, Optional, Callable, Any, TypeVar
from datetime import datetime
from github import Github
from github.GithubException import RateLimitExceededException, UnknownObjectException
from pkg_resources import parse_version
from wheel_inspect import inspect_wheel
from py4a.api.requirements import Requirements
from py4a.api.static import get_apis_from_wheel
from py4a.api.dynamic import get_apis_from_runtime
from py4a.api.accessor import (
    METADATA_PATH,
    RELEASE_NOTE_PATH,
    PKG_PATH,
    STATIC_API_PATH,
    DYNAMIC_API_PATH,
    REQ_PATH,
)


T = TypeVar("T")
logger = logging.getLogger(__name__)


def _is_valid_version(ver: str) -> bool:
    try:
        v = parse_version(ver)
        if v.is_prerelease or v.is_devrelease:
            return False
        return True
    except ValueError:
        pass
    return False


def _page_num(per_page: int, total_count: int) -> int:
    """Calculate total number of pages given page size and total number of items"""
    assert per_page > 0 and total_count >= 0
    if total_count % per_page == 0:
        return total_count // per_page
    return total_count // per_page + 1


def _request_github(
    gh: Github, gh_func: Callable[[], T], default: Any = None
) -> Optional[T]:
    """
    This is a wrapper to ensure that any rate-consuming interactions with GitHub
      have proper exception handling.
    """
    for _ in range(0, 3):  # Max retry 3 times
        try:
            data = gh_func()
            return data
        except RateLimitExceededException as ex:
            logging.info("{}: {}".format(type(ex), ex))
            sleep_time = gh.rate_limiting_resettime - time.time() + 10
            logging.info(
                "Rate limit reached, wait for {} seconds...".format(sleep_time)
            )
            time.sleep(max(1.0, sleep_time))
        except UnknownObjectException as ex:
            logging.error("{}: {}".format(type(ex), ex))
            break
        except Exception as ex:
            logging.error("{}: {}".format(type(ex), ex))
            time.sleep(5)
    return default


def _select_wheel(file_info: List[dict]) -> Optional[dict]:
    result = None
    result_py_ver = ""
    for i in file_info:
        if not i["filename"] or not i["filename"].endswith(".whl"):
            continue
        # Parse wheel file name according to https://www.python.org/dev/peps/pep-0427/
        tags = i["filename"].split("-")
        if len(tags) <= 4 or len(tags) >= 7:  # bad filename
            continue
        elif len(tags) == 5:
            py_ver, platform = tags[2], tags[4]
        else:
            py_ver, platform = tags[3], tags[5]
        if ("any" in platform or "linux" in platform) and py_ver > result_py_ver:
            result = i
            result_py_ver = py_ver
    return result


def _write_apis(api_dir: str, apis: List[entity.Package]) -> None:
    os.makedirs(api_dir, exist_ok=True)
    for pkg in apis:
        if os.sep in pkg.name:
            continue  # This is a workaround for handling '/' in top level
        json_filename = os.path.join(api_dir, f"{pkg.name}.json.zip")
        txt_filename = os.path.join(api_dir, f"{pkg.name}.txt")
        with zipfile.ZipFile(json_filename, "w", zipfile.ZIP_LZMA) as f:
            f.writestr(f"{pkg.name}.json", jsonpickle.encode(pkg))
        with open(txt_filename, "w") as f:
            f.write("\n".join(sorted(pkg.keys())))


def _get_api_statistics(apis: Dict[str, entity.Package]) -> Dict[str, Any]:
    stat = {
        "top_levels": list(apis.keys()),
        "num_apis": sum(len(x.keys()) for x in apis.values()),
        "num_modules": sum(len(x.modules()) for x in apis.values()),
        "num_functions": 0,
        "num_classes": 0,
        "num_variables": 0,
        "num_aliases": 0,
    }
    for x in apis.values():
        for k in x.keys():
            if k in x:
                e = x[k]
                if isinstance(e, entity.Function):
                    stat["num_functions"] += 1
                if isinstance(e, entity.Class):
                    stat["num_classes"] += 1
                if isinstance(e, entity.Variable):
                    stat["num_variables"] += 1
                if isinstance(e, (entity.Alias, entity.WildcardAlias)):
                    stat["num_aliases"] += 1
    return stat


def _extract_api_dynamic_worker(
    pkg: str, ver: str, pkg_dir: str, api_dir: str
) -> Dict[str, Any]:
    status = {
        "package": pkg,
        "version": ver,
        "time_begin": datetime.now().isoformat(),
        "time_end": None,
        "failed_modules": None,
        "error": False,
        "error_message": None,
        "stack_trace": None,
        "api_statistics": None,
    }
    try:
        v_dir = os.path.join(pkg_dir, ver)

        wheel_paths = [p for p in os.listdir(v_dir) if p.endswith(".whl")]
        if len(wheel_paths) == 0:
            logger.warning(f"{pkg}-{ver}: cannot find supported wheel file")
            status["time_end"] = datetime.now().isoformat()
            status["error"] = True
            status["error_message"] = "cannot find supported wheel file"
            return status

        wheel_metadata = inspect_wheel(os.path.join(v_dir, wheel_paths[0]))
        top_levels = [pkg]
        if "top_level" in wheel_metadata["dist_info"]:
            top_levels = wheel_metadata["dist_info"]["top_level"]
        logger.debug(f"{pkg}-{ver} top levels: {top_levels}")

        packages, failed_modules = get_apis_from_runtime(pkg, ver, top_levels)

        _write_apis(os.path.join(api_dir, ver), packages.values())
        with open(os.path.join(api_dir, ver, "failed_modules.json"), "w") as f:
            json.dump(failed_modules, f)

        status["time_end"] = datetime.now().isoformat()
        status["failed_modules"] = failed_modules
        status["api_statistics"] = _get_api_statistics(packages)
        logger.info(f"{pkg}-{ver}: finished extracting APIs using dynamic analysis")
    except Exception as ex:
        status["time_end"] = datetime.now().isoformat()
        status["error"] = True
        status["error_message"] = f"{type(ex)}: {ex}"
        status["stack_trace"] = traceback.format_exc()
        logger.error(
            f"{pkg}-{ver}: failed to extract APIs using dynamic analysis\n"
            f"{ex}: {traceback.format_exc()}"
        )
    return status


def download_release_notes(
    pkg_name: str, repo_name: str, rn_dir: str
) -> Dict[str, bool]:
    """Download release notes from a GitHub repository (for a Python package).

    Args:
        pkg_name (str): The name of the Python package.
        repo_name (str): Repository name in "owner/name" format.
        rn_dir (str): A directory where all release notes will be stored.
            A folder with foler name same to `pkg_name` will be created in this directory.

    Returns:
        Dict[str, bool]: version -> whether download is successful
    """
    logger.info(f"{pkg_name}: downloading release notes")

    rn_dir = pathlib.Path(rn_dir).joinpath(pkg_name)
    rn_dir.mkdir(parents=True, exist_ok=True)

    result = {}
    gh = Github()
    repo = _request_github(gh, lambda: gh.get_repo(repo_name))
    releases = _request_github(gh, lambda: repo.get_releases())
    page_num = _page_num(gh.per_page, releases.totalCount)
    for i in range(0, page_num):
        for release in _request_github(gh, lambda: releases.get_page(i)):
            if not _is_valid_version(release.tag_name):
                result[release.tag_name] = False
                continue
            with open(
                rn_dir.joinpath(release.tag_name + ".md"), "w", encoding="utf-8"
            ) as f:
                f.write(release.body)
            result[release.tag_name] = True
    return result


def download_package(pkg_name: str, metadata_dir: str, pkg_dir: str) -> Dict[str, bool]:
    """Download all metadata and a selected wheel for all versions of a Python package.

    Select and only download the wheel that supports Linux and uses the latest Python version.
    This selection is to optimize download time and minimize storage requirements.

    Args:
        pkg_name (str): Name of the python package.
        metadata_dir (str): A directory where all metadata information will be stored.
            A folder with folder name same to `pkg_name` will be created in this directory.
        pkg_dir (str): A directory where all package wheels will be stored.
            A folder with folder name same to `pkg_name` will be created in this directory.

    Returns:
        Dict[str, bool]: version -> whether download is successful
    """
    result = {}

    metadata_dir = pathlib.Path(metadata_dir).joinpath(pkg_name)
    pkg_dir = pathlib.Path(pkg_dir).joinpath(pkg_name)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Collect all metadata
    logger.info(f"{pkg_name}: downloading metadata")

    try:
        pypi_info = requests.get(f"https://pypi.org/pypi/{pkg_name}/json").json()
    except json.decoder.JSONDecodeError:
        logger.error(f"{pkg_name}: does not exist on PyPI")
        return {}
    with open(os.path.join(metadata_dir, pkg_name + ".json"), "w") as f:
        json.dump(pypi_info, f, indent=2)
    for ver in pypi_info["releases"]:
        if not _is_valid_version(ver):
            result[ver] = False
            continue
        if os.path.exists(metadata_dir.joinpath(ver + ".json")):
            continue
        ver_info = requests.get(f"https://pypi.org/pypi/{pkg_name}/{ver}/json").json()
        with open(metadata_dir.joinpath(ver + ".json"), "w") as f:
            json.dump(ver_info, f, indent=2)

    # Collect wheels
    logger.info(f"{pkg_name}: downloading wheels")
    for ver, file_info in pypi_info["releases"].items():
        if not _is_valid_version(ver):
            continue
        whl_file = _select_wheel(file_info)
        logger.debug(f"{ver}: {whl_file['filename'] if whl_file else None}")
        if whl_file is not None:
            ver_path = pkg_dir.joinpath(ver)
            ver_path.mkdir(parents=True, exist_ok=True)
            if ver_path.joinpath(whl_file["filename"]).exists():
                logger.debug(
                    f"Skipping {whl_file['filename']} because file already exists"
                )
            else:
                wget.download(whl_file["url"], str(ver_path))
            result[ver] = True
        else:
            result[ver] = False

    return result


def extract_api_static(pkg_name: str, pkg_dir: str, api_dir: str) -> Dict[str, Any]:
    """Extract APIs for all versions in a Python package, using static analysis.

    Args:
        pkg_name (str): Name of the Python package
        pkg_dir (str): The directory where all package wheels are stored.
            A folder named `pkg_name` should exist in `pkg_dir`.
        api_dir (str): A directory where API information will be stored.
            This directory will be created if it does not exist.
            A folder with folder name same as `pkg_name` will be created in this directory.
            For each package version, a JSON file describing its APIs will be stored.

    Returns:
        Dict[str, Any]: version -> detailed info about the extraction
    """
    logger.info(f"{pkg_name}: extracting APIs using static analysis")

    pkg_dir = os.path.join(pkg_dir, pkg_name)
    api_dir = os.path.join(api_dir, pkg_name)
    if not os.path.isdir(pkg_dir):
        raise ValueError(f"{pkg_dir} is not a directory")
    pathlib.Path(api_dir).mkdir(parents=True, exist_ok=True)

    versions = os.listdir(pkg_dir)
    versions.sort(key=lambda x: parse_version(x))
    status = {}

    for v in versions:
        status[v] = {
            "package": pkg_name,
            "version": v,
            "time_begin": datetime.now().isoformat(),
            "time_end": None,
            "failed_modules": None,
            "error": False,
            "error_message": None,
            "stack_trace": None,
            "api_statistics": None,
        }
        try:
            v_dir = os.path.join(pkg_dir, v)

            wheel_paths = [p for p in os.listdir(v_dir) if p.endswith(".whl")]
            if len(wheel_paths) == 0:
                logger.warning(f"{pkg_name}-{v}: cannot find supported wheel file")
                status[v]["error"] = True
                status[v]["error_message"] = "cannot find supported wheel file"
                continue

            packages = get_apis_from_wheel(
                pkg_name, os.path.join(v_dir, wheel_paths[0])
            )

            _write_apis(os.path.join(api_dir, v), packages)

            status[v]["time_end"] = datetime.now().isoformat()
            status[v]["failed_modules"] = deepcopy(static.failed_modules)
            status[v]["api_statistics"] = _get_api_statistics(
                {p.name: p for p in packages}
            )
            logger.info(
                f"{pkg_name}-{v}: finished extracting APIs using static analysis"
            )
        except Exception as ex:
            status[v]["time_end"] = datetime.now().isoformat()
            status[v]["error"] = True
            status[v]["error_message"] = f"{type(ex)}: {ex}"
            status[v]["stack_trace"] = traceback.format_exc()
            logger.error(
                f"{pkg_name}-{v}: failed to extract APIs using static analysis\n"
                f"{ex}: {traceback.format_exc()}"
            )
    return status


def extract_api_dynamic(
    pkg_name: str, pkg_dir: str, api_dir: str, num_workers: int = 8
) -> Dict[str, Any]:
    """Extract APIs for all versions in a Python package, using dynamic analysis.

    Args:
        pkg_name (str): Name of the Python package
        pkg_dir (str): The directory where all package wheels are stored.
            A folder named `pkg_name` should exist in `pkg_dir`.
        api_dir (str): A directory where API information will be stored.
            This directory will be created if it does not exist.
            A folder with folder name same as `pkg_name` will be created in this directory.
            For each package version, a JSON file describing its APIs will be stored.
        num_workers (int): Number of workers in process pool.

    Returns:
        Dict[str, Any]: version -> detailed info about the extraction
    """
    logger.info(f"{pkg_name}: extracting APIs using dynamic analysis")

    pkg_dir = os.path.join(pkg_dir, pkg_name)
    api_dir = os.path.join(api_dir, pkg_name)
    if not os.path.isdir(pkg_dir):
        raise ValueError(f"{pkg_dir} is not a directory")
    pathlib.Path(api_dir).mkdir(parents=True, exist_ok=True)

    versions = os.listdir(pkg_dir)
    versions.sort(key=lambda x: parse_version(x))
    params = [(pkg_name, v, pkg_dir, api_dir) for v in reversed(versions)]

    with mp.Pool(num_workers) as pool:
        results = pool.starmap(_extract_api_dynamic_worker, params)
    return {r["version"]: r for r in results}


def extract_requirements(pkg_name: str, pkg_dir: str, req_dir: str) -> Dict[str, bool]:
    """Extract requirement information (i.e., Python version and package dependenies)

    Args:
        pkg_name (str): The package name to extract
        pkg_dir (str): The directory where all package wheels are stored.
            A folder named `pkg_name` should exist in `pkg_dir`.
        req_dir (str): A directory where requirement information will be stored.
            For each package version, a JSON file describing its requirements will be stored.

    Raises:
        ValueError: if `pkg_dir` does not exist.

    Returns:
        Dict[str, bool]: version -> whether extraction is successful
    """
    logger.info(f"{pkg_name}: extracting requirements")

    pkg_dir = os.path.join(pkg_dir, pkg_name)
    req_dir = os.path.join(req_dir, pkg_name)
    if not os.path.isdir(pkg_dir):
        raise ValueError(f"{pkg_dir} is not a directory")
    pathlib.Path(req_dir).mkdir(parents=True, exist_ok=True)

    versions = os.listdir(pkg_dir)
    versions.sort(key=lambda x: parse_version(x))
    status = {}
    for v in versions:
        v_dir = os.path.join(pkg_dir, v)
        v_output_dir = os.path.join(req_dir, v)
        pathlib.Path(v_output_dir).mkdir(parents=True, exist_ok=True)

        wheel_path = os.path.join(v_dir, os.listdir(v_dir)[0])
        requirements = Requirements(pkg_name, v, wheel_path)
        output_file = os.path.join(v_output_dir, "requirements.json")
        with open(output_file, "w") as f:
            f.write(jsonpickle.encode(requirements))
        status[v] = True
        logger.info(f"{pkg_name}-{v}: finished extracting requirements")

    return status


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("pkg_name")
    parser.add_argument("repo_name")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    download_release_notes(args.pkg_name, args.repo_name, RELEASE_NOTE_PATH)
    download_package(args.pkg_name, METADATA_PATH, PKG_PATH)
    summary_static = extract_api_static(args.pkg_name, PKG_PATH, STATIC_API_PATH)
    summary_dynamic = extract_api_dynamic(args.pkg_name, PKG_PATH, DYNAMIC_API_PATH)
    extract_requirements(args.pkg_name, PKG_PATH, REQ_PATH)
    with open(f"{args.pkg_name}-static-api-summary.json", "w") as f:
        json.dump(summary_static, f, indent=2)
    with open(f"{args.pkg_name}-dynamic-api-summary.json", "w") as f:
        json.dump(summary_dynamic, f, indent=2)
