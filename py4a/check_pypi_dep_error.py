import os
import json
import logging
import argparse
import pkg_resources
import pandas as pd
import multiprocessing as mp
import py4a.api.accessor as accessor
import py4a.client.analyzer as analyzer
import py4a.client.checker as checker

from collections import defaultdict
from traceback import format_exc
from tqdm import tqdm


pkg_ver_with_apis_static = defaultdict(set)
pkg_ver_with_apis_dynamic = defaultdict(set)


def check(pkg_name: str, pkg_ver: str, dynamic: bool, out_dir: str):
    global pkg_ver_with_apis_static
    global pkg_ver_with_apis_dynamic
    pkg_ver_with_apis = (
        pkg_ver_with_apis_dynamic if dynamic else pkg_ver_with_apis_static
    )

    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
        handlers=[logging.FileHandler(f"logs/check/check-{os.getpid()}.log")],
    )

    if os.path.exists(os.path.join(out_dir, "summary", f"{pkg_name}-{pkg_ver}.json")):
        logging.info(f"{pkg_name}-{pkg_ver} already checked")
        return

    all_violations, all_matches = [], []
    wheel_path = accessor.get_wheel_path(pkg_name, pkg_ver)
    api_access_patterns = analyzer.get_api_access_chains_from_wheel(wheel_path)

    logging.info(f"Checking {pkg_name}-{pkg_ver}...")
    summary = {
        "package": pkg_name,
        "version": pkg_ver,
        "dynamic": dynamic,
        "out_dir": out_dir,
        "deps": [],
        "num_violations": 0,
        "num_matches": 0,
    }

    req = accessor.get_requirements(pkg_name, pkg_ver)
    if len(req.require_deps) == 0:
        logging.info(f"{pkg_name}-{pkg_ver} has no dependency")
        return

    for dep in req.require_deps:
        spec = dep.name + ("" if dep.specifier == "" else f"({dep.specifier})")
        spec = pkg_resources.Requirement.parse(spec)

        try:
            vers = accessor.get_vers(dep.name)
        except ValueError:
            vers = []

        vers_with_apis = []
        for ver in pkg_ver_with_apis[dep.name]:
            if pkg_resources.parse_version(ver) in spec:
                vers_with_apis.append(ver)

        summary["deps"].append(
            {
                "spec": dep.to_dict(),
                "vers": vers,
                "vers_with_apis": vers_with_apis,
            }
        )

        if len(vers_with_apis) == 0:
            continue

        curr_violations = []
        logging.info(f"  Checking {pkg_name}-{pkg_ver}: {spec}")
        for ver in vers_with_apis:
            logging.info(
                f"  {pkg_name}-{pkg_ver} may require {dep.name}-{ver}, check compatibility..."
            )
            dependent_apis = accessor.get_apis(dep.name, ver, dynamic)
            result = checker.check_tree(api_access_patterns, dependent_apis)
            for src_file, matches in result.items():
                for access_chain, match in matches:
                    if match.status in [
                        analyzer.MatchStatus.MISMATCH,
                        analyzer.MatchStatus.MISSING,
                    ]:
                        curr_violations.append(
                            {
                                "package": pkg_name,
                                "version": pkg_ver,
                                "dep_pkg": dep.name,
                                "dep_spec": dep.specifier,
                                "dep_ver": ver,
                                "src_file": src_file,
                                "line_nums": list(sorted(access_chain.line_nums)),
                                "access_chain": str(access_chain),
                                "violation": match.status.value,
                                "message": match.message,
                                "vers_occurred": None,
                                "vers_with_apis": len(vers_with_apis),
                                "prob": None,
                            }
                        )
                        summary["num_violations"] += 1
                    else:
                        summary["num_matches"] += 1

        for violation in curr_violations:
            vers_occurred = set()
            for another in curr_violations:
                if another["message"] == violation["message"]:
                    vers_occurred.add(another["dep_ver"])
            violation["vers_occurred"] = len(vers_occurred)
            violation["prob"] = 1 - len(vers_occurred) / len(vers_with_apis)
            all_violations.append(violation)

    if len(all_violations) > 0:
        logging.info(f"{len(all_violations)} violations found for {pkg_name}-{pkg_ver}")
        with open(
            os.path.join(out_dir, "violations", f"{pkg_name}-{pkg_ver}.json"), "w"
        ) as f:
            json.dump(all_violations, f, indent=2)
    with open(os.path.join(out_dir, "summary", f"{pkg_name}-{pkg_ver}.json"), "w") as f:
        json.dump(summary, f, indent=2)


def work(*args, **kwargs):
    try:
        check(*args, **kwargs)
    except Exception as e:
        logging.error(f"{e}: {format_exc()}")
        exit(-1)


def check_all(args):
    global pkg_ver_with_apis_static
    global pkg_ver_with_apis_dynamic

    pkg = pd.read_csv("data/pypi_downloads_last_180_days_20211117.csv").head(args.limit)
    pkg_stats = pd.DataFrame(sum(accessor.get_stats_all().values(), []))

    for k in pkg_stats[
        pkg_stats.summary_static.map(lambda x: x is not None and not x["error"])
    ].itertuples():
        pkg_ver_with_apis_static[k.package].add(k.version)
    for k in pkg_stats[
        pkg_stats.summary_dynamic.map(lambda x: x is not None and not x["error"])
    ].itertuples():
        pkg_ver_with_apis_dynamic[k.package].add(k.version)

    pkg_stats = pkg_stats[~pkg_stats.wheel.isna() & pkg_stats.package.isin(pkg.project)]

    pkg2download = dict(zip(pkg.project, pkg.num_downloads))
    pkg_stats["downloads"] = pkg_stats.package.map(pkg2download)
    pkg_stats.sort_values(by="downloads", ascending=False, inplace=True)
    logging.info(pkg_stats.head())

    logging.info(
        f"Checking dependency error for {len(pkg)} packages ({len(pkg_stats)} versions)..."
    )
    os.makedirs("output/static/summary", exist_ok=True)
    os.makedirs("output/static/violations", exist_ok=True)
    os.makedirs("output/dynamic/summary", exist_ok=True)
    os.makedirs("output/dynamic/violations", exist_ok=True)
    os.makedirs("logs/check", exist_ok=True)
    with mp.Pool(mp.cpu_count() // 3) as pool:
        output_dir = "output/static" if not args.dynamic else "output/dynamic"
        pool.starmap(
            work,
            zip(
                pkg_stats.package,
                pkg_stats.version,
                [args.dynamic] * len(pkg_stats),
                [output_dir] * len(pkg_stats),
            ),
        )


def load_json(file):
    with open(file, "r") as f:
        return json.load(f)


def summarize_all():
    data = {"static": defaultdict(list), "dynamic": defaultdict(list)}

    pkg2download = pd.read_csv("data/pypi_downloads_last_180_days_20211117.csv")
    pkg2download = {
        p: c for p, c in zip(pkg2download.project, pkg2download.num_downloads)
    }

    pkg2summary = defaultdict(list)
    files = [
        os.path.join("output/dynamic/summary", file)
        for file in os.listdir("output/dynamic/summary")
    ]
    with mp.Pool(mp.cpu_count()) as pool:
        result = pool.map(load_json, files)
    for summary in result:
        pkg2summary[summary["package"]].append(summary)

    for pkg, summaries in pkg2summary.items():
        logging.info("Summarizing %s...", pkg)
        summaries = sorted(
            summaries,
            key=lambda x: pkg_resources.parse_version(x["version"]),
            reverse=True,
        )
        for summary in summaries[0:10]:  # Currenly, only inspect the first
            if summary["num_violations"] == 0:
                continue

            dep2vers = {
                dep["spec"]["name"]: sorted(
                    dep["vers_with_apis"], key=pkg_resources.parse_version
                )
                for dep in summary["deps"]
            }

            with open(
                f"output/dynamic/violations/{pkg}-{summary['version']}.json", "r"
            ) as f:
                violations = json.load(f)

            logging.info(
                f"{pkg}-{summary['version']}: {len(violations)} violations found"
            )

            vio_by_msg = defaultdict(list)
            for vio in violations:
                vio_by_msg[
                    (vio["version"], vio["dep_pkg"], vio["dep_ver"], vio["message"])
                ].append(vio)

            vio_by_msg2 = []
            for (ver, dep_pkg, dep_ver, message), vios in vio_by_msg.items():
                if vios[0]["violation"] == "MISSING":
                    continue
                if vios[0]["prob"] < 0.5:
                    continue
                if all(vio["dep_ver"] != dep2vers[vio["dep_pkg"]][-1] for vio in vios):
                    continue
                data["dynamic"]["violations"].append(
                    {
                        "package": pkg,
                        "downloads": pkg2download[pkg],
                        "version": ver,
                        "dep_pkg": dep_pkg,
                        "dep_spec": vios[0]["dep_spec"],
                        "matched_vers": len(dep2vers[dep_pkg]),
                        "dep_ver": dep_ver,
                        "violation": vios[0]["violation"],
                        "message": message,
                        "confidence": vios[0]["prob"],
                        "affected": "\n".join(
                            [
                                vio["src_file"] + ":" + str(vio["line_nums"])
                                for vio in vios
                            ]
                        ),
                    }
                )
            # msg2dep_vers = defaultdict(set)
            # for vio in vio_by_msg2:
            # msg2dep_vers[(vio["dep_pkg"], vio["message"])].add(vio["dep_ver"])
            # msg = set()
            # for vio in vio_by_msg2:
            #    vio["confidence"] = 1 - len(msg2dep_vers[(vio["dep_pkg"], vio["message"])]) / vio["matched_vers"]
            #    if vio["confidence"] >= 0.8 and vio["dep_ver"] == dep2vers[vio["dep_pkg"]][-1]:
            #        msg.add(vio["message"])
            # for vio in vio_by_msg2:
            #    if vio["message"] in msg:
            # data["dynamic"]["violations"].append(vio)

    pd.DataFrame(data["dynamic"]["violations"]).sort_values(
        by=["downloads", "version", "message"], ascending=[False, True, True]
    ).to_csv("output/dynamic/violations.csv", index=False)


def main():
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--dynamic", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()

    if args.summarize:
        summarize_all()
    else:
        check_all(args)

    logging.info("Done!")


if __name__ == "__main__":
    main()
