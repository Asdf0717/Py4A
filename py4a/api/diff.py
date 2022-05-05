"""Diffing two Python package versions to get all API changes

This file implements the following paper:
  Zhang, Zhaoxu, et al. 
  "How do Python framework APIs evolve? an exploratory study." 
  2020 IEEE 27th International Conference on Software Analysis, 
  Evolution and Reengineering (SANER). IEEE, 2020.
"""

from enum import Enum
from typing import Dict, List, Optional
from py4a.api.entity import (
    Entity,
    Package,
    Class,
    Function,
    Variable,
    Alias,
    WildcardAlias,
)


class DiffType(Enum):
    ClsAdd = "Class Addition"
    ClsRem = "Class Removal"
    FuncAdd = "Function Addition"
    FuncRem = "Function Removal"
    ReqParamAdd = "Required Parameter Addition"
    ReqParamRem = "Required Parameter Removal"
    OptParamAdd = "Optional Parameter Addition"
    OptParamRem = "Optional Parameter Removal"
    ParamReorder = "Parameter Reordering"
    ParamDefValAdd = "Parameter Default Value Addition"
    ParamDefValRem = "Parameter Default Value Removal"
    ParamDefValChg = "Parameter Default Value Change"
    VarAdd = "Variable Addition"
    VarRem = "Variable Removal"


class Diff(object):
    """Object representing an API change

    Attributes:
        diff_type (DiffType): the type of diff
        api_name (str): The full name of changed API
    The following three attributes are only used for API changes related to parameters:
        param (str): The parameter that changed
        old_value (str): The old default value (if default value change)
            or position (if reordering) of the parameter
        new_value (str): The new default value (if default value change)
            or position (if reordering) of the parameter
    The following attributes are related to breaking change impact:
        clients_total (int): number of total clients
        clients_used (int): number of clients using the API
        clients_impacted (int): number of impacted clients
    """

    def __init__(
        self,
        diff_type: DiffType,
        api_name: str,
        param: str = None,
        old_value: str = None,
        new_value: str = None,
        clients_total: int = 0,
        clients_used: int = 0,
        clients_impacted: int = 0,
    ):
        self.diff_type: DiffType = diff_type
        self.api_name: str = api_name
        self.param: str = param
        self.old_value: str = old_value
        self.new_value: str = new_value
        self.clients_total: int = clients_total
        self.clients_used: int = clients_used
        self.clients_impacted: int = clients_impacted

    @property
    def is_breaking(self):
        return self.diff_type in [
            DiffType.ClsRem,
            DiffType.FuncRem,
            DiffType.VarRem,
            DiffType.ReqParamAdd,
            DiffType.ReqParamRem,
            DiffType.OptParamAdd,
            DiffType.OptParamRem,
            DiffType.ParamReorder,
            DiffType.ParamDefValAdd,
            DiffType.ParamDefValRem,
            DiffType.ParamDefValChg,
        ]

    def __str__(self):
        if self.diff_type == DiffType.ClsAdd:
            return f"`{self.api_name}`: class added"
        elif self.diff_type == DiffType.ClsRem:
            return f"`{self.api_name}`: class removed"
        elif self.diff_type == DiffType.FuncAdd:
            return f"`{self.api_name}`: function added"
        elif self.diff_type == DiffType.FuncRem:
            return f"`{self.api_name}`: function removed"
        elif self.diff_type == DiffType.ReqParamAdd:
            return f"`{self.api_name}`: required parameter `{self.param}` added"
        elif self.diff_type == DiffType.ReqParamRem:
            return f"`{self.api_name}`: required parameter `{self.param}` removed"
        elif self.diff_type == DiffType.ParamReorder:
            return f"`{self.api_name}`: parameter `{self.param}` reordered"
        elif self.diff_type == DiffType.OptParamAdd:
            return f"`{self.api_name}`: optional parameter `{self.param}` added"
        elif self.diff_type == DiffType.OptParamRem:
            return f"`{self.api_name}`: optional parameter `{self.param}` removed"
        elif self.diff_type == DiffType.ParamDefValAdd:
            return f"`{self.api_name}`: default value `{self.new_value}` added to `{self.param}`"
        elif self.diff_type == DiffType.ParamDefValRem:
            return f"`{self.api_name}`: default value `{self.old_value}` removed from `{self.param}`"
        elif self.diff_type == DiffType.ParamDefValChg:
            return f"`{self.api_name}`: default value changed from `{self.old_value}` to `{self.new_value}` in `{self.param}`"
        elif self.diff_type == DiffType.VarAdd:
            return f"`{self.api_name}`: variable added"
        elif self.diff_type == DiffType.VarRem:
            return f"`{self.api_name}`: variable removed"
        else:
            raise ValueError(f"Unknown diff type {self.diff_type}")

    def __repr__(self):
        return str(self)


def same_default_value(v1: str, v2: str) -> bool:
    """Apply heuristics to determine whether default value has changed during API evolution"""
    if v1.startswith("<") and v2.startswith("<"):
        return True
    if "(" in v1 and "(" in v2 and v1.split("(")[0] == v2.split("(")[0]:
        return True
    if v1 == v2:
        return True
    return False


def diff_function(old: Function, new: Function, full_name: str) -> List[Diff]:
    """Diff two functions"""
    diffs = []

    p_all = {"old": set(), "new": set()}
    opt = {"old": set(), "new": set()}
    p2def = {"old": {}, "new": {}}
    p2pos = {"old": {}, "new": {}}
    for key, api in (("old", old), ("new", new)):
        for pos, param in enumerate(api.args):
            p_all[key].add(param.name)
            if param.default is not None:
                opt[key].add(param.name)
                p2def[key][param.name] = param.default
            p2pos[key][param.name] = pos

    for p in p_all["new"] - p_all["old"]:
        if p in opt["new"]:
            diffs.append(Diff(DiffType.OptParamAdd, full_name, p))
        else:
            diffs.append(Diff(DiffType.ReqParamAdd, full_name, p))

    for p in p_all["old"] - p_all["new"]:
        if p in opt["old"]:
            diffs.append(Diff(DiffType.OptParamRem, full_name, p))
        else:
            diffs.append(Diff(DiffType.ReqParamRem, full_name, p))

    for p in p_all["old"] & p_all["new"]:
        if p in opt["old"] and p not in opt["new"]:
            diffs.append(
                Diff(DiffType.ParamDefValAdd, full_name, p, p2def["old"][p], None)
            )
        if p not in opt["old"] and p in opt["new"]:
            diffs.append(
                Diff(DiffType.ParamDefValRem, full_name, p, None, p2def["new"][p])
            )
        if (
            p in opt["old"]
            and p in opt["new"]
            and not same_default_value(p2def["old"][p], p2def["new"][p])
        ):
            diffs.append(
                Diff(
                    DiffType.ParamDefValChg,
                    full_name,
                    p,
                    p2def["old"][p],
                    p2def["new"][p],
                )
            )
        if p2pos["old"][p] != p2pos["new"][p]:
            diffs.append(
                Diff(
                    DiffType.ParamReorder,
                    full_name,
                    p,
                )
            )

    return diffs


def diff_class(old: Class, new: Class, full_name: str) -> List[Diff]:
    """Diff two classes"""
    diffs = []
    vars = {
        "old": {v.name: v for v in old.fields + old.static_fields},
        "new": {v.name: v for v in new.fields + new.static_fields},
    }
    funcs = {
        "old": {f.name: f for f in old.methods},
        "new": {f.name: f for f in new.methods},
    }
    for v_name in set(vars["old"].keys()) - set(vars["new"].keys()):
        diffs.append(Diff(DiffType.VarRem, full_name + "." + v_name))
    for v_name in set(vars["new"].keys()) - set(vars["old"].keys()):
        diffs.append(Diff(DiffType.VarAdd, full_name + "." + v_name))
    for f_name in set(funcs["old"].keys()) - set(funcs["new"].keys()):
        diffs.append(Diff(DiffType.FuncRem, full_name + "." + f_name))
    for f_name in set(funcs["new"].keys()) - set(funcs["old"].keys()):
        diffs.append(Diff(DiffType.FuncAdd, full_name + "." + f_name))
    for f_name in set(funcs["new"].keys()) & set(funcs["old"].keys()):
        old_func, new_func = funcs["old"][f_name], funcs["new"][f_name]
        if not isinstance(old_func, Function) or not isinstance(new_func, Function):
            # It is possible some function cannot get signature from dynamic analysis
            continue
        diffs.extend(diff_function(old_func, new_func, full_name + "." + f_name))
    return diffs


def diff_entity(
    old: Optional[Entity], new: Optional[Entity], full_name: str
) -> List[Diff]:
    """Diff two entities.

    The two entities must be of the same type, either Class, Function, Variable or Alias.

    Args:
        old (Entity): The old API entity, can be None.
        new (Entity): The new API entity, can be None.
        full_name (str): The fully qualified name of the API.

    Raises:
        ValueError: When the two entities are of different type.

    Returns:
        List[Diff]: A list of API diffs.
    """
    if isinstance(old, (Alias, WildcardAlias)) or isinstance(
        new, (Alias, WildcardAlias)
    ):
        return []  # make an conservative approximation
    if old is None:
        if isinstance(new, Class):
            diff_type = DiffType.ClsAdd
        elif isinstance(new, Function):
            diff_type = DiffType.FuncAdd
        elif isinstance(new, Variable):
            diff_type = DiffType.VarAdd
        else:
            raise ValueError(f"Cannot diff between None and {type(new)}")
        return [Diff(diff_type, full_name)]
    elif new is None:
        if isinstance(old, Class):
            diff_type = DiffType.ClsRem
        elif isinstance(old, Function):
            diff_type = DiffType.FuncRem
        elif isinstance(old, Variable):
            diff_type = DiffType.VarRem
        else:
            raise ValueError(f"Cannot diff between {type(old)} and None")
        return [Diff(diff_type, full_name)]
    else:
        if type(old) != type(new):
            raise ValueError(f"Cannot diff between {type(old)} and {type(new)}")
        if isinstance(old, Function) and isinstance(new, Function):
            return diff_function(old, new, full_name)
        elif isinstance(old, Class) and isinstance(new, Class):
            return diff_class(old, new, full_name)
    return []


def diff_pkg(old: Dict[str, Package], new: Dict[str, Package]) -> List[Diff]:
    """Diff two Python packages.

    Args:
        old (Dict[str, Package]): The old API for the Python package.
        new (Dict[str, Package]): The new API for the Python package.

    Returns:
        List[Diff]: A list of API diffs.
    """
    diffs = []

    for mod_name in set(old.keys()) - set(new.keys()):
        for key in old[mod_name].keys():
            try:
                diffs.extend(diff_entity(old[mod_name][key], None, key))
            except (KeyError, ValueError):
                continue
    for mod_name in set(new.keys()) - set(old.keys()):
        for key in new[mod_name].keys():
            try:
                diffs.extend(diff_entity(None, new[mod_name][key], key))
            except (KeyError, ValueError):
                continue
    for mod_name in set(old.keys()) & set(new.keys()):
        old_keys, new_keys = set(old[mod_name].keys()), set(new[mod_name].keys())
        for key in old_keys - new_keys:
            try:
                diffs.extend(diff_entity(old[mod_name][key], None, key))
            except (KeyError, ValueError):
                continue
        for key in new_keys - old_keys:
            try:
                diffs.extend(diff_entity(None, new[mod_name][key], key))
            except (KeyError, ValueError):
                continue
        for key in old_keys & new_keys:
            try:
                if type(old[mod_name][key]) == type(new[mod_name][key]):
                    diffs.extend(
                        diff_entity(old[mod_name][key], new[mod_name][key], key)
                    )
            except KeyError:
                continue

    return diffs
