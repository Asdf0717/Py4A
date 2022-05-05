import logging

from typing import List, Dict, Tuple
from py4a.api.entity import Package
from py4a.client.analyzer import AccessChain, MatchResult, MatchStatus


logger = logging.getLogger(__name__)


def check(
    access_chains: List[AccessChain], package: Dict[str, Package]
) -> List[Tuple[AccessChain, MatchResult]]:
    """Check whether a list of API access chains matches API usages in a certain Python package

    If an access chain does not access APIs in the package top levels, it will be ignored.
    For example, when checking API accesses for `pandas`, a call to `numpy.mean()` will be ignored.

    Args:
        access_chains (List[AccessChain]): The list of access chains.
        package (Dict[str, Package]): A data structure representing APIs in a package.
            For example, as obtained using `py4a.api.accessor.get_apis()`.

    Returns:
        List[Tuple[AccessChain, MatchResult]]: A list of match results.
    """
    matches = []
    for c in access_chains:
        if c.top_level not in package:
            continue
        match_result = c.match(package)
        matches.append((c, match_result))
    return matches


def check_tree(
    access_chains: Dict[str, List[AccessChain]], package: Dict[str, Package]
) -> Dict[str, List[Tuple[AccessChain, MatchResult]]]:
    """Check whether a dict of API access chains matches API usages in a certain package.

    Typically, the dict key is a source file and each list represents API accesses in this file.
    The whole dict represents all API accesses from a Python project folder tree.

    Args:
        access_chains (Dict[str, List[AccessChain]]): The dict of access chains
        package (Dict[str, Package]): A data structure representing APIs in a package.
            For example, as obtained using `py4a.api.accessor.get_apis()`.

    Returns:
        Dict[str, List[MatchResult]]: A dict of match results.
    """
    violations = {}
    for key, access_chain in access_chains.items():
        violations[key] = check(access_chain, package)
    return violations
