import os
import logging
import traceback
import pandas as pd
import multiprocessing as mp

from typing import Dict, Any
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from py4a.api.entity import *
from py4a.api.extractor import *
from py4a.api.accessor import *
from py4a.api.requirements import *


def get_pkg_stats(
    pkg_name: str, summary_static: Dict[str, Any], summary_dynamic: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Get stats for all versions in a package"""
    stats = []
    try:
        releases = get_metadata(pkg_name)["releases"]
    except ValueError:
        return stats
    for ver, files in releases.items():
        if len(files) > 0:
            time = min(parse_date(f["upload_time"]) for f in files).isoformat()
        else:
            time = None
        try:
            ver_info = get_metadata_ver(pkg_name, ver)["info"]
        except ValueError:
            continue
        req_py = ver_info["requires_python"] if "requires_python" in ver_info else None
        req_dist = ver_info["requires_dist"] if "requires_dist" in ver_info else None
        whl_path = get_wheel_path(pkg_name, ver)
        whl_top_levels = None
        if whl_path is not None:
            whl_metadata = inspect_wheel(whl_path)
            if "top_level" in whl_metadata["dist_info"]:
                whl_top_levels = whl_metadata["dist_info"]["top_level"]
        whl_path = os.path.basename(whl_path) if whl_path is not None else None
        stat = {
            "package": pkg_name,
            "version": ver,
            "time": time,
            "requires_python": req_py,
            "requires_dist": req_dist,
            "wheel": whl_path,
            "wheel_top_levels": whl_top_levels,
            "summary_static": summary_static[ver] if ver in summary_static else None,
            "summary_dynamic": summary_dynamic[ver] if ver in summary_dynamic else None,
        }
        stats.append(stat)
    return stats


def get_package_data(pkg_name: str):
    stat_path = os.path.join(STAT_PATH, f"{pkg_name}.json")
    if os.path.exists(stat_path):
        logging.info(f"Skipping {pkg_name} as its data have been extracted")
        return
    try:
        download_package(pkg_name, METADATA_PATH, PKG_PATH)
        summary_static = extract_api_static(pkg_name, PKG_PATH, STATIC_API_PATH)
        extract_requirements(pkg_name, PKG_PATH, REQ_PATH)
        stats = get_pkg_stats(pkg_name, summary_static, {})
        with open(stat_path, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        logging.error(
            f"Error while extracting APIs for {pkg_name}: {traceback.format_exc()}"
        )


def get_dynamic_data(pkg_name: str):
    stat_path = os.path.join(STAT_PATH, f"{pkg_name}.json")
    try:
        stats = get_stats(pkg_name)
    except ValueError:
        logging.error(f"{pkg_name} does not have static statistics")
        return
    if any(stat["summary_dynamic"] is not None for stat in stats):
        logging.info(f"Skipping {pkg_name} as its dynamic data have been extracted")
        return
    try:
        summary_dynamic = extract_api_dynamic(pkg_name, PKG_PATH, DYNAMIC_API_PATH)
        for stat in stats:
            if stat["version"] in summary_dynamic:
                stat["summary_dynamic"] = summary_dynamic[stat["version"]]
        with open(stat_path, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        logging.error(
            f"Error while extracting APIs for {pkg_name}: {traceback.format_exc()}"
        )


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    os.makedirs(STAT_PATH, exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--dynamic", action="store_true")
    args = parser.parse_args()

    projects = (
        pd.read_csv("data/pypi_downloads_last_180_days_20211117.csv")
        .fillna("")
        .head(args.limit)
    )

    count = Counter()
    for pkg_name in projects.project:
        if has_metadata(pkg_name):
            count["metadata"] += 1
        if has_api(pkg_name, dynamic=False):
            count["static_api"] += 1
        if has_api(pkg_name, dynamic=True):
            count["dynamic_api"] += 1
    logging.info(count)

    if not args.dynamic:
        with mp.Pool(mp.cpu_count()) as pool:
            pool.map(get_package_data, projects.project)
    else:
        with ProcessPoolExecutor(max_workers=mp.cpu_count() // 8) as pool:
            pool.map(get_dynamic_data, projects.project)

    logging.info("Finish!")
