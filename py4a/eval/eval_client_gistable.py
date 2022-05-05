"""
Load the Gistable dataset published in:
1. Horton, Eric, and Chris Parnin. "Gistable: Evaluating the executability of python code snippets on github." 
2018 IEEE International Conference on Software Maintenance and Evolution (ICSME). IEEE, 2018.
"""

import os
import ast
import random
import logging
import numpy as np
import pandas as pd
import py4a.api.accessor as accessor
import py4a.client.analyzer as analyzer

from tqdm import tqdm


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    if not os.path.exists("../gistable"):
        os.system("git clone https://github.com/gistable/gistable.git ../gistable")

    logging.info("Loading package imports and stdlib")
    packages = pd.read_csv("data/packages.csv")
    pkg_stats = pd.read_csv("data/pkg_stats.csv")
    stdlib_apis = accessor.get_stdlib_apis(ver="3.9.6")
    all_imports = set(
        sum(pkg_stats.top_levels.dropna().map(lambda x: x.split(" ")), [])
    )

    # Select code snippets that:
    # 1. Can parse with Python 3.9 AST module
    # 2. Contain only imports in Python std lib and top 100 packages
    logging.info("Selecting Gistable snippets")
    lines = []
    codes = []
    for path in tqdm(os.listdir("../gistable/all-gists")):
        file = os.path.join("../gistable/all-gists", path, "snippet.py")
        if not os.path.exists(file):
            logging.error(f"{file} does not exist!")
            continue

        with open(file, "r") as f:
            code = f.read()

        try:
            tree = ast.parse(code)
        except Exception as ex:
            continue

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for name in node.names:
                    imports.add(name.name.split(".")[0])

        if all(i not in stdlib_apis and i not in all_imports for i in imports):
            continue

        lines.append(len(code.split("\n")))
        codes.append(code)

    logging.info(f"LOC of the snippets: \n{pd.Series(lines).describe()}")

    logging.info(f"Sampling snippets and analyzing client API usages...")
    random.seed(114514)
    os.makedirs("evaluation/gistable", exist_ok=True)
    codes = [code for code in codes if len(code.split("\n")) <= np.median(lines)]
    results = []
    for i, code in enumerate(random.sample(codes, min(len(codes), 100))):
        with open(os.path.join("evaluation/gistable", f"{i}.py"), "w") as f:
            f.write(code)
        tree = ast.parse(code)
        access_chains = analyzer.get_api_access_chains(code)
        for chain in access_chains:
            results.append({"id": i, "access_chain": chain})
    pd.DataFrame(results).to_csv("evaluation/access_chains.csv", index=False)

    logging.info("Finish!")
