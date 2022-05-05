import json
import random
import logging
import subprocess
import pandas as pd

from typing import Set, List, Tuple
from py4a.api.entity import Class, Function, Alias, WildcardAlias
from py4a.api.accessor import *
from py4a.api.extractor import *


logger = logging.getLogger(__name__)


def list_conda_envs() -> Set[str]:
    result = json.loads(
        subprocess.run(
            ["conda", "info", "--envs", "--json"],
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8", "ignore")
    )
    envs = set()
    for env in result["envs"]:
        for dir in result["envs_dirs"]:
            if env.startswith(dir):
                envs.add(os.path.relpath(env, dir))
    return env


def create_env(env_name: str, packages: List[str] = []) -> bool:
    if env_name in list_conda_envs():
        logger.info(f"Environment {env_name} already exists")
        return False
    subprocess.run(["conda", "create", "-y", "--name", env_name, "python=3.9"])
    for pkg in packages:
        result = subprocess.run(
            ["conda", "run", "-n", env_name, "python", "-m", "pip", "install", pkg]
        )
        if result.returncode != 0:
            logger.error(f"Failed to install {pkg}")
            return False
    return True


def execute_script(env_name: str, script_path: str, args: List[str] = []) -> str:
    return subprocess.run(
        ["conda", "run", "-n", env_name, "python", script_path, *args],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8", "ignore")


def remove_env(env_name: str):
    subprocess.run(["conda", "remove", "-y", "--name", env_name, "--all"])


def evaluate_precision(
    pkg_names: List[str], dynamic: bool = False
) -> List[Dict[str, Any]]:
    results = []

    for pkg_name in pkg_names:
        if not has_metadata(pkg_name) or not has_api(pkg_name, dynamic):
            logger.info(f"{pkg_name} extraction failed, skipping")
            continue

        vers = get_vers_with_apis(pkg_name, dynamic)
        if len(vers) == 0:
            logger.info(f"No API extracted for {pkg_name}")
            continue
        apis = get_apis(pkg_name, vers[-1], dynamic)
        logger.info(f"Top level packages: {apis.keys()}")
        logger.info(f"{sum(len(v.keys()) for v in apis.values())} API names")

        api_names: List[Tuple[str, Package]] = []
        for top_level, pkg in apis.items():
            for api_name in pkg.keys():
                if api_name in pkg and isinstance(pkg[api_name], (Function, Class)):
                    api_names.append((api_name, pkg))
        random.shuffle(api_names)
        api_names = api_names[:50]

        conda_env = f"py4a-{pkg_name}-{vers[-1]}"
        if conda_env in list_conda_envs():
            logger.info(f"Environment {conda_env} already exists, removing")
            remove_env(conda_env)

        if not create_env(conda_env, [f"{pkg_name}=={vers[-1]}"]):
            logger.info(f"Environment {conda_env} creation failed, skipping")
            continue

        for api_name, pkg in api_names:
            logger.info(f"Testing {api_name}")
            api_type = "other"
            if isinstance(pkg[api_name], Function):
                api_type = "function"
            if isinstance(pkg[api_name], Class):
                api_type = "class"
            result = execute_script(
                conda_env, "py4a/eval/try_access_api.py", [api_name, api_type]
            ).strip()
            logger.info(result)
            results.append(
                {
                    "package": pkg_name,
                    "version": vers[-1],
                    "api": api_name,
                    "type": api_type,
                    "success": True if "OK" in result else False,
                    "stdout": result,
                }
            )
        remove_env(conda_env)

    return results


def evaluate_recall(
    pkg_names: List[str], dynamic: bool = False
) -> List[Dict[str, Any]]:
    results = []

    for pkg_name in pkg_names:
        if not has_metadata(pkg_name) or not has_api(pkg_name, dynamic):
            logger.info(f"{pkg_name} extraction failed, skipping")
            continue

        vers = get_vers_with_apis(pkg_name, dynamic)
        if len(vers) == 0:
            logger.info(f"No API extracted for {pkg_name}")
            continue

        conda_env = f"py4a-{pkg_name}-{vers[-1]}"
        if conda_env in list_conda_envs():
            logger.info(f"Environment {conda_env} already exists, removing")
            remove_env(conda_env)

        if not create_env(conda_env, [f"{pkg_name}=={vers[-1]}"]):
            logger.info(f"Environment {conda_env} creation failed, skipping")
            continue

        apis = get_apis(pkg_name, vers[-1], dynamic)
        runtime = get_runtime(pkg_name, vers[-1], py_ver="3.9.6")
        logger.info(f"{pkg_name}-{vers[-1]} runtime modules: {list(runtime.keys())}")

        for top_level in apis.keys():
            top_level_apis = json.loads(
                execute_script(conda_env, "py4a/eval/collect_apis.py", [top_level])
            )
            logger.info(
                f"{pkg_name}-{vers[-1]} {top_level}.*: {len(top_level_apis)} APIs"
            )
            for name, api_type in top_level_apis:
                if name not in apis[top_level]:
                    extracted_type = "Missing"
                elif isinstance(apis[top_level][name], (Alias, WildcardAlias)):
                    try:
                        extracted_type = type(
                            apis[top_level].get(name, top_levels=runtime)
                        ).__name__
                    except KeyError:
                        extracted_type = "Unresolved"
                else:
                    extracted_type = type(apis[top_level][name]).__name__
                results.append(
                    {
                        "package": pkg_name,
                        "version": vers[-1],
                        "api": name,
                        "dynamic_type": api_type,
                        "extracted_type": extracted_type,
                    }
                )

        remove_env(conda_env)

    return results


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    packages = pd.read_csv("data/pypi_downloads_last_180_days_20211117.csv").fillna("")

    results = evaluate_precision(packages.head(100).project, dynamic=True)
    pd.DataFrame(results).to_csv("evaluation/apid_precision.csv", index=False)
    results = evaluate_recall(packages.head(100).project, dynamic=True)
    pd.DataFrame(results).to_csv("evaluation/apid_recall.csv", index=False)

    results = evaluate_precision(packages.head(100).project, dynamic=False)
    pd.DataFrame(results).to_csv("evaluation/apis_precision.csv", index=False)
    results = evaluate_recall(packages.head(100).project, dynamic=False)
    pd.DataFrame(results).to_csv("evaluation/apis_recall.csv", index=False)

    logger.info("Finish!")
