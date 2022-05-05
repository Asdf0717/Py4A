"""Utilities for handing dependency specifications in PyPI packages"""

import re
from packaging.requirements import Requirement


def get_spec_type(requires_dist: str) -> str:
    """Determine the type of a dependency specification

    Adopted from https://bitbucket.org/jensdietrich/lib.io-study/src/master/mapping-rules/Pypi.rules
      which is the artifact of Dietrich, Jens, et al. "Dependency versioning in the wild."
      2019 IEEE/ACM 16th International Conference on Mining Software Repositories (MSR).
      IEEE, 2019.
    """
    req = Requirement(requires_dist)
    specs = list(iter(req.specifier))
    if len(specs) == 0:
        return "any"
    elif len(specs) == 1:
        op, ver = specs[0].operator, specs[0].version
        if ">=" == op or ">" == op:
            return "at-least"
        elif "<=" == op or "<" == op:
            return "at-most"
        elif "==" == op:
            if re.match(r"\d+\.\d+\.\*", ver):
                return "var-micro"
            elif re.match(r"\d+\.\*", ver):
                return "var-minor"
            elif ver == "*":
                return "any"
            else:
                return "fixed"
        elif "~=" == op:
            if re.match(r"\d+\.\d+\.\d+", ver):
                return "var-micro"
            elif re.match(r"\d+\.\d+", ver):
                return "var-minor"
            else:
                return "other"
        else:
            return "other"
    elif len(specs) == 2:
        ops = set((specs[0].operator, specs[1].operator))
        if (">" in ops or ">=" in ops) and ("<" in ops or "<=" in ops):
            return "range"
        else:
            return "other"
    return "other"
