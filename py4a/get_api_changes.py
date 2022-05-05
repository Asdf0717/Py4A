import os
import logging
import argparse
import json
import jsonpickle
import multiprocessing as mp
import py4a.api.accessor as accessor
import py4a.api.entity as entity
import py4a.client.analyzer as analyzer

from typing import List, Tuple, Dict
from collections import Counter, defaultdict
from pkg_resources import parse_version
from py4a.api.diff import Diff, diff_pkg


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--packages",
        help="comma delimited list of packages, e.g., pandas,matplotlib,numpy",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--output-dir",
        help="directory for output",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--dynamic",
        help="whether to use dynamic API data",
        action="store_true",
    )
    parser.add_argument(
        "--client",
        help="consider client usage during breaking change analysis",
        action="store_true",
    )
    args = parser.parse_args()
    logging.info(args)
    return args


def find_dependents(pkgs: List[str], output_dir: str) -> Dict[str, List[dict]]:
    api_usage_dir = os.path.join(output_dir, "api-usage-all")
    dependents = defaultdict(list)
    for file in os.listdir(api_usage_dir):
        if file.endswith(".json"):
            logging.info(file)
            with open(os.path.join(api_usage_dir, file)) as f:
                data = json.load(f)
            if data["u_pkg"] in pkgs:
                dependents[data["u_pkg"]].append(data)
    return dependents


def estimate_client_usage(
    v1: str,
    v2: str,
    apis1: Dict[str, entity.Package],
    apis2: Dict[str, entity.Package],
    diffs: List[Diff],
    clients: List[dict],
) -> List[Tuple[Diff, int, int]]:
    for diff in diffs:
        used, all_clients = 0, 0
        for client in clients:
            if client["u_ver"] != v1:
                continue
            all_clients += 1
            for api in client["api_stats"].keys():
                if api == diff.api_name:
                    used += 1
                    for pattern in client["api_stats"][api]["patterns"]:
                        try:
                            chain = analyzer.AccessChain._from_str(pattern)
                            if (
                                chain.match(apis1).status == analyzer.MatchStatus.MATCH
                                and chain.match(apis2).status
                                != analyzer.MatchStatus.MATCH
                            ):
                                diff.clients_impacted += 1
                            break
                        except Exception as ex:
                            logging.error(f"{pattern} in {v1}-{v2} causing {ex}")
        diff.clients_used = used
        diff.clients_total = all_clients
    return diffs


def generate_release_notes(pkg: str, v1: str, v2: str, diffs: List[Diff]) -> str:
    bcs = sorted(
        [d for d in diffs if d.is_breaking],
        key=lambda d: (-d.clients_used, str(d)),
    )
    nbcs = sorted(
        [d for d in diffs if not d.is_breaking],
        key=lambda d: (-d.clients_used, str(d)),
    )
    bc_summ = Counter([d.diff_type for d in bcs])
    nbc_summ = Counter([d.diff_type for d in nbcs])
    rn = f"# Release Note for {pkg} {v1} to {v2}\n"
    rn += """
## Change Summary

| Breaking?    | Change Type                      | Count     |
| ------------ | -------------------------------- | --------- |
"""
    for t, cnt in sorted(bc_summ.items(), key=lambda x: x[0].value):
        rn += f"| **Breaking** | {t.value:32} | {cnt:9} |\n"
    for t, cnt in sorted(nbc_summ.items(), key=lambda x: x[0].value):
        rn += f"| Non-Breaking | {t.value:32} | {cnt:9} |\n"
    rn += "\n## Breaking Changes\n\n"
    for i, diff in enumerate(bcs):
        rn += f"{i + 1}. {diff} (impacts {diff.clients_impacted} of {diff.clients_used} clients, {diff.clients_total} clients in total) \n"
    rn += "\n## Non-Breaking Changes\n\n"
    for i, diff in enumerate(nbcs):
        rn += f"{i + 1}. {diff}\n"
    rn += "\n"
    return rn


def output_results(
    output_dir: str, pkg: str, v1: str, v2: str, diffs: List[Diff], rn: str
):
    diff_dir = os.path.join(output_dir, "api-changes", pkg)
    rn_dir = os.path.join(output_dir, "release-notes", pkg)
    os.makedirs(diff_dir, exist_ok=True)
    os.makedirs(rn_dir, exist_ok=True)
    with open(os.path.join(diff_dir, f"{v1}-{v2}.json"), "w") as f:
        f.write(jsonpickle.dumps(diffs, indent=2))
    with open(os.path.join(rn_dir, f"{v1}-{v2}.md"), "w") as f:
        f.write(rn)


def get_api_changes(
    output_dir: str, pkg: str, v1: str, v2: str, dynamic: bool, clients: List[dict]
):
    logging.info(f"{pkg}: analyzing {v1} - {v2}")
    apis1 = accessor.get_apis(pkg, v1, dynamic=dynamic)
    apis2 = accessor.get_apis(pkg, v2, dynamic=dynamic)
    diffs = diff_pkg(apis1, apis2)
    diffs = estimate_client_usage(v1, v2, apis1, apis2, diffs, clients)
    rn = generate_release_notes(pkg, v1, v2, diffs)
    output_results(output_dir, pkg, v1, v2, diffs, rn)


def main():
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    pkgs = args.packages.split(",")

    if args.client:
        dependents = find_dependents(pkgs, args.output_dir)
    else:
        dependents = defaultdict(list)

    # Get api changes
    func_params = []
    for pkg in pkgs:
        vers = sorted(
            accessor.get_vers_with_apis(pkg, dynamic=args.dynamic), key=parse_version
        )
        logging.info(f"{pkg}: {vers}")
        for i in range(0, len(vers) - 1):
            v1, v2 = vers[i], vers[i + 1]
            func_params.append(
                (args.output_dir, pkg, v1, v2, args.dynamic, dependents[pkg])
            )
    with mp.Pool(mp.cpu_count() // 2) as pool:
        pool.starmap(get_api_changes, func_params)

    logging.info("Finish!")


if __name__ == "__main__":
    main()
