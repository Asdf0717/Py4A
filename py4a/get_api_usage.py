import os
import json
import logging
import argparse
import resource
import traceback
import pandas as pd
import multiprocessing as mp
import py4a.api.accessor as accessor
import py4a.client.analyzer as analyzer
import py4a.client.checker as checker

from typing import List, Dict, Any
from collections import defaultdict
from pkg_resources import parse_version, Requirement


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Whether to overwrite existing client information",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Whether to select clients for all versions (for breaking change analysis)"
        " or only the latest version (for API usage analysis)",
    )
    parser.add_argument(
        "-p",
        "--packages",
        help="comma delimited list of packages, e.g., pandas,matplotlib,numpy",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--dynamic",
        help="whether to use dynamic API data",
        action="store_true",
    )
    parser.add_argument(
        "--output-dir",
        help="directory for output",
        type=str,
        required=True,
    )
    args = parser.parse_args()
    logging.info(args)
    return args


def match_spec(pkg: str, spec: str, ver: str):
    spec = pkg + ("" if spec == "" else f"({spec})")
    spec = Requirement.parse(spec)
    return ver in spec


def find_clients(client_pkg: str, upstream_pkgs: List[str]) -> List[Dict[str, Any]]:
    try:
        vers = accessor.get_vers_with_reqs(client_pkg)

        client_info = []
        for ver in vers:
            reqs = accessor.get_requirements(client_pkg, ver)
            for req in reqs.require_deps:
                if req.name in upstream_pkgs:
                    logging.info(f"{client_pkg}-{ver}: {req.name} ({req.specifier})")
                    client_info.append((ver, req.name, req.specifier))

        result = []
        for ver, u_pkg, u_spec in client_info:
            u_vers = accessor.get_vers_with_apis(u_pkg)
            u_vers = [v for v in u_vers if match_spec(u_pkg, u_spec, v)]
            u_vers_before = [
                v
                for v in u_vers
                if accessor.get_release_time(u_pkg, v)
                < accessor.get_release_time(client_pkg, ver)
            ]
            result.append(
                {
                    "c_pkg": client_pkg,
                    "c_ver": ver,
                    "u_pkg": u_pkg,
                    "u_spec": u_spec,
                    "u_ver_published": sorted(u_vers_before, key=parse_version)[-1],
                    "u_ver_current": sorted(u_vers, key=parse_version)[-1],
                    "u_vers": ",".join(u_vers),
                }
            )
        return result
    except Exception as e:
        logging.error(f"{client_pkg} failed: {e}")
        return []


def select_clients(args):
    upstream_pkgs = args.packages.split(",")
    client_pkgs = pd.read_csv("data/pypi_downloads_last_180_days_20211117.csv").head(
        args.limit
    )
    with mp.Pool(mp.cpu_count()) as pool:
        results = pool.starmap(
            find_clients, [(p, upstream_pkgs) for p in client_pkgs.project]
        )
        results = pd.DataFrame(sum(results, [])).sort_values(by=["u_pkg", "c_pkg"])
    results.to_csv(os.path.join(args.output_dir, "client.csv"), index=False)


def select_client_for_api_analysis(args):
    upstream_pkgs = args.packages.split(",")
    clients = pd.read_csv(os.path.join(args.output_dir, "client.csv"))
    sampled_clients = []
    for u_pkg in upstream_pkgs:
        pkg_clients = clients[clients.u_pkg == u_pkg]
        spec2client = defaultdict(list)
        for u_spec, c_pkg, c_ver in zip(
            pkg_clients.u_spec, pkg_clients.c_pkg, pkg_clients.c_ver
        ):
            spec2client[(u_spec, c_pkg)].append(c_ver)
        for (u_spec, c_pkg), c_vers in spec2client.items():
            c_ver = sorted(c_vers, key=parse_version)[-1]
            sampled_clients.append(
                {
                    "u_pkg": u_pkg,
                    "u_spec": u_spec,
                    "c_pkg": c_pkg,
                    "c_ver": c_ver,
                }
            )
    for c in sampled_clients:
        row = clients[
            (clients.u_pkg == c["u_pkg"])
            & (clients.c_pkg == c["c_pkg"])
            & (clients.c_ver == c["c_ver"])
        ]
        c["u_ver_current"] = row.u_ver_current.values[0]
        c["u_vers"] = row.u_vers.values[0]
    pd.DataFrame(sampled_clients).to_csv(
        os.path.join(args.output_dir, "client_sampled.csv"), index=False
    )


def get_api_usage(
    output_dir: str,
    overwrite: bool,
    dynamic: bool,
    u_pkg: str,
    u_ver: str,
    c_pkg: str,
    c_ver: str,
):
    try:
        output_file = os.path.join(output_dir, f"{u_pkg},{u_ver},{c_pkg},{c_ver}.json")
        if os.path.exists(output_file) and not overwrite:
            logging.info(f"{output_file} exists, skipping")
            return

        apis = accessor.get_apis(u_pkg, u_ver, dynamic=dynamic)
        wheel_path = accessor.get_wheel_path(c_pkg, c_ver)
        api_access_patterns = analyzer.get_api_access_chains_from_wheel(
            wheel_path, list(apis.keys())
        )
        api_matches = checker.check_tree(api_access_patterns, apis)
        api_stats = defaultdict(lambda: {"files": 0, "calls": 0, "patterns": set()})
        violations = []
        for src_file, matches in api_matches.items():
            for access_chain, match in matches:
                if match.status == analyzer.MatchStatus.MATCH:
                    api_stats[match.matched_name]["files"] += 1
                    api_stats[match.matched_name]["calls"] += len(
                        access_chain.line_nums
                    )
                    api_stats[match.matched_name]["patterns"].add(access_chain.chain_str)
                else:
                    violations.append(
                        {
                            "src_file": src_file,
                            "access_chain": str(access_chain),
                            "match": match.status.value,
                            "message": match.message,
                        }
                    )
        for api, stats in api_stats.items():
            api_stats[api]["patterns"] = sorted(stats["patterns"])

        logging.info(
            f"{u_pkg}-{u_ver} at {c_pkg}-{c_ver}: {len(api_stats)} APIs used, {len(violations)} violations"
        )
        with open(output_file, "w") as f:
            json.dump(
                {
                    "u_pkg": u_pkg,
                    "u_ver": u_ver,
                    "c_pkg": c_pkg,
                    "c_ver": c_ver,
                    "api_stats": dict(api_stats),
                    "violations": violations,
                },
                f,
            )
    except Exception as e:
        logging.error(f"{e}: {traceback.format_exc()}")


def get_api_usage_latest(args):
    clients = pd.read_csv(os.path.join(args.output_dir, "client_sampled.csv"))

    folder = "dynamic" if args.dynamic else "static"
    output_dir = os.path.join(args.output_dir, folder, "api-usage-latest")
    os.makedirs(output_dir, exist_ok=True)

    params = []
    for pkg in args.packages.split(","):
        pkg_clients = clients[clients.u_pkg == pkg]
        latest_ver = sorted(pkg_clients.u_ver_current.unique(), key=parse_version)[-1]
        pkg_clients = pkg_clients[pkg_clients.u_ver_current == latest_ver]
        for row in pkg_clients.itertuples():
            params.append(
                (
                    output_dir,
                    args.overwrite,
                    args.dynamic,
                    row.u_pkg,
                    row.u_ver_current,
                    row.c_pkg,
                    row.c_ver,
                )
            )

    with mp.Pool(mp.cpu_count() // 2, maxtasksperchild=1) as pool:
        pool.starmap(get_api_usage, params)


def get_api_usage_all(args):
    clients = pd.read_csv(os.path.join(args.output_dir, "client_sampled.csv"))
    folder = "dynamic" if args.dynamic else "static"
    output_dir = os.path.join(args.output_dir, folder, "api-usage-all")
    os.makedirs(output_dir, exist_ok=True)
    params = []
    for row in clients.itertuples():
        for u_ver in row.u_vers.split(","):
            params.append(
                (
                    output_dir,
                    args.overwrite,
                    args.dynamic,
                    row.u_pkg,
                    u_ver,
                    row.c_pkg,
                    row.c_ver,
                )
            )
    logging.info(f"{len(params)} clients to process")
    with mp.Pool(mp.cpu_count() // 2, maxtasksperchild=1) as pool:
        pool.starmap(get_api_usage, params)


def main():
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    resource.setrlimit( # Max memory per process: 16 GB
        resource.RLIMIT_AS, (16 * 1024 * 1024 * 1024, resource.RLIM_INFINITY)
    )

    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    client_file = os.path.join(args.output_dir, "client.csv")
    client_sampled_file = os.path.join(args.output_dir, "client_sampled.csv")
    if not os.path.exists(client_file) or args.overwrite:
        select_clients(args)
    if not os.path.exists(client_sampled_file) or args.overwrite:
        select_client_for_api_analysis(args)

    if not args.all:
        get_api_usage_latest(args)
    else:
        get_api_usage_all(args)

    logging.info("Done!")


if __name__ == "__main__":
    main()
