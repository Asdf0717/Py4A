from os import access
import py4a.api.static as static
import py4a.client.analyzer as analyzer
import py4a.client.checker as checker

from py4a.client.analyzer import MatchStatus


code = """
import pandas as pd
df = pd.read_csv(ababab="ababab")
pd.DataFrame().to_markdown()
"""


def test_check():
    packages = static.get_apis_from_wheel(
        "pandas",
        "tests/resource/pandas-1.3.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    )
    packages = {p.name: p for p in packages}
    access_chains = analyzer.get_api_access_chains(code)
    results = checker.check(access_chains, packages)
    print(results)
    assert results[2][1].status == MatchStatus.MISMATCH
    for access_chain, match_result in results:
        if str(access_chain).startswith("pandas.DataFrame().to_markdown()"):
            assert match_result.matched_name == "pandas.DataFrame.to_markdown"


def test_check_wheel():
    packages = static.get_apis_from_wheel(
        "pyOpenSSL",
        "tests/resource/pyOpenSSL-21.0.0-py2.py3-none-any.whl",
    )
    packages = {p.name: p for p in packages}
    api_access_patterns = analyzer.get_api_access_chains_from_wheel(
        "tests/resource/urllib3-1.26.7-py2.py3-none-any.whl"
    )
    results = checker.check_tree(api_access_patterns, packages)
    for f, result in results.items():
        if len(result) == 0:
            continue
        print(f, result)
