"""Minimal wrappers for accessing downloaded package data"""

import os
import json
import zipfile
import jsonpickle
import pkg_resources

from typing import List, Dict, Optional, Any
from datetime import datetime
from dateutil.parser import parse as parse_date
from py4a.api.requirements import Requirements
from py4a.api.entity import Package
from py4a.api.stdlib import get_stdlib_apis


RELEASE_NOTE_PATH = "data/release-notes"
METADATA_PATH = "data/metadata"
PKG_PATH = "data/pkg"
STATIC_API_PATH = "data/apis"
DYNAMIC_API_PATH = "data/apid"
REQ_PATH = "data/requirements"
STAT_PATH = "data/stats"


def has_metadata(pkg_name: str) -> bool:
    """Check whether the package metadata are already present"""
    try:
        vers = get_vers(pkg_name)
        return len(vers) != 0
    except ValueError:
        return False


def has_req(pkg_name: str) -> bool:
    """Check whether the package requirement data are already present"""
    try:
        vers = get_vers_with_reqs(pkg_name)
        return len(vers) != 0
    except (ValueError, FileNotFoundError):
        return False


def has_api(pkg_name: str, dynamic: bool = False) -> bool:
    """Check whether the package APIs are already present"""
    try:
        vers = get_vers_with_apis(pkg_name, dynamic)
        return len(vers) != 0
    except (ValueError, FileNotFoundError):
        return False


def get_stats_all() -> Dict[str, List[Dict[str, Any]]]:
    """Get statistics for all packages"""
    stats = {}
    for filename in os.listdir(STAT_PATH):
        pkg_name = filename.replace(".json", "")
        stats[pkg_name] = get_stats(pkg_name)
    return stats


def get_stats(pkg_name: str) -> List[Dict[str, Any]]:
    """Get statistics for a package"""
    stats_dir = os.path.join(STAT_PATH, pkg_name + ".json")
    if not os.path.exists(stats_dir):
        raise ValueError(f"{pkg_name} does not have statistics")
    with open(stats_dir, "r") as f:
        stats = json.load(f)
    return stats


def get_vers(pkg_name: str) -> List[str]:
    """Get available versions of a package, sorted by release date"""
    releases = get_metadata(pkg_name)["releases"]
    ver_date = []
    for ver, files in releases.items():
        if len(files) == 0:
            continue
        time = min(parse_date(f["upload_time"]) for f in files)
        ver_date.append((ver, time))
    ver_date.sort(key=lambda x: x[1])
    return [v for v, _ in ver_date]


def get_vers_with_apis(pkg_name: str, dynamic: bool = False) -> List[str]:
    """Get versions of a package with API data available, sorted by release date"""
    api_dir = DYNAMIC_API_PATH if dynamic else STATIC_API_PATH
    api_dir = os.path.join(api_dir, pkg_name)
    api_vers = set(os.listdir(api_dir))
    results = []
    for v in get_vers(pkg_name):
        if v not in api_vers:
            continue
        if os.listdir(os.path.join(api_dir, v)) == ["failed_modules.json"]:
            continue
        results.append(v)
    return results


def get_vers_with_reqs(pkg_name: str) -> List[str]:
    """Get versions of a package with requirement data available, sorted by release date"""
    req_dir = os.path.join(STATIC_API_PATH, pkg_name)
    req_vers = set(os.listdir(req_dir))
    return list(filter(lambda v: v in req_vers, get_vers(pkg_name)))


def get_metadata(pkg_name: str) -> Dict[str, Any]:
    """Get metadata (the JSON document retrieved from PyPI) for a package"""
    meta_dir = os.path.join(METADATA_PATH, pkg_name, pkg_name + ".json")
    if not os.path.exists(meta_dir):
        raise ValueError(f"{pkg_name} does not have metadata")
    with open(meta_dir, "r") as f:
        meta = json.load(f)
    return meta


def get_metadata_ver(pkg_name: str, ver: str) -> Dict[str, Any]:
    """Get metadata (the JSON document retrieved from PyPI) for a package version"""
    meta_dir = os.path.join(METADATA_PATH, pkg_name, ver + ".json")
    if not os.path.exists(meta_dir):
        raise ValueError(f"{pkg_name} does not have metadata for version {ver}")
    with open(meta_dir, "r") as f:
        meta = json.load(f)
    return meta


def get_release_time(pkg_name: str, ver: str) -> datetime:
    """Get the release time of a package version (i.e., the earliest upload time of its files)"""
    meta = get_metadata_ver(pkg_name, ver)
    return min(parse_date(f["upload_time"]) for f in meta["releases"][ver])


def get_apis(pkg_name: str, ver: str, dynamic: bool = False) -> Dict[str, Package]:
    """Get APIs for a package version, returns top level -> Package

    For example, matplotlib 3.4.3 have three top level packages:
       `pylab`, `matplotlib`, and `mpl_toolkits`.
    The top level package names will be dict keys and the APIs will be dict values.
    """
    path = DYNAMIC_API_PATH if dynamic else STATIC_API_PATH
    api_dir = os.path.join(path, pkg_name, ver)
    if not os.path.exists(api_dir):
        raise ValueError(f"{pkg_name} does not have API data for version {ver}")
    api_files = list(filter(lambda x: x.endswith(".json.zip"), os.listdir(api_dir)))
    apis = {}
    for api_file in api_files:
        top_level = api_file.replace(".json.zip", "")
        with zipfile.ZipFile(
            os.path.join(api_dir, api_file), "r", zipfile.ZIP_LZMA
        ) as f:
            apis[top_level] = jsonpickle.decode(
                f.read(top_level + ".json").decode("utf-8")
            )
    return apis


def get_failed_modules(
    pkg_name: str, ver: str, dynamic: bool = False
) -> Dict[str, str]:
    path = DYNAMIC_API_PATH if dynamic else STATIC_API_PATH
    path = os.path.join(path, pkg_name, ver, "failed_modules.json")
    if not os.path.exists(path):
        raise ValueError(
            f"{pkg_name} does not have failed module data for version {ver}"
        )
    with open(path, "r") as f:
        failed_modules = json.load(f)
    return failed_modules


def get_wheel_path(pkg_name: str, ver: str) -> Optional[str]:
    """Get full (absolute) wheel path for a package version"""
    path = os.path.join(PKG_PATH, pkg_name, ver)
    if not os.path.exists(path):
        return None
    for file in os.listdir(path):
        if file.endswith(".whl"):
            return os.path.abspath(os.path.join(path, file))
    return None


def get_requirements(pkg_name: str, ver: str) -> Requirements:
    """Get requirements for a package version"""
    req_dir = os.path.join(REQ_PATH, pkg_name, ver, "requirements.json")
    if not os.path.exists(req_dir):
        raise ValueError(f"{pkg_name} does not have requirement for version {ver}")
    with open(req_dir, "r") as f:
        reqs = jsonpickle.decode(f.read())
    return reqs


def resolve_dependencies(req: Requirements) -> Dict[str, str]:
    """Resolve dependencies given requirements provided by a package version"""
    resolved_deps: Dict[str, str] = {}
    res_queue = list(req.require_deps)
    while len(res_queue) > 0:
        dep = res_queue.pop(0)
        if dep.name in resolved_deps:
            continue
        if not has_api(dep.name):
            continue
        spec = dep.name + ("" if dep.specifier == "" else f"({dep.specifier})")
        spec = pkg_resources.Requirement.parse(spec)
        vers = get_vers_with_reqs(dep.name)
        for ver in reversed(vers):
            if pkg_resources.parse_version(ver) not in spec:
                continue
            try:
                reqs = get_requirements(dep.name, ver)
            except ValueError:
                continue
            resolved_deps[dep.name] = ver
            res_queue.extend(reqs.require_deps)
            break
    return resolved_deps


def get_runtime(
    pkg_name: str, ver: str, py_ver: str, dynamic: bool = False
) -> Dict[str, Package]:
    """Get all runtime APIs for a package version"""
    req = get_requirements(pkg_name, ver)
    resolved_deps = resolve_dependencies(req)
    runtime = get_apis(pkg_name, ver, dynamic)
    for n, p in get_stdlib_apis(py_ver, dynamic=dynamic).items():
        if n not in runtime:
            runtime[n] = p
    for p, v in resolved_deps.items():
        if v not in get_vers_with_apis(p, dynamic):
            continue
        for top_level, api in get_apis(p, v, dynamic).items():
            if top_level not in runtime:
                runtime[top_level] = api
    return runtime
