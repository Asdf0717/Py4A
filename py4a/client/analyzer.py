"""Extract API access chains from Python source code"""

from __future__ import annotations

import os
import ast
import logging
import zipfile

from enum import Enum
from typing import List, Dict, Optional, Union, Set, Tuple
from collections import defaultdict
from py4a.api.entity import Entity, Function, Class, Package


logger = logging.getLogger(__name__)


class Call(object):
    """An object representing an API call

    For example: read_csv(str, int, index=bool)

    Attributes:
        name (str): the name of the call
        args (int): number of positional arguments
        kwargs (Set[str]): number of explicitly specified keyword arguments
        starargs (bool): whether starargs are provided
             (i.e. *args, which indiates any number of positional arguments provided by runtime variables)
        additional_kwargs (bool): whether additional keyword arguments are provided
             (i.e., **kwargs, which indiates any number of keyword arguments provided by runtime variables)
    """

    def __init__(
        self,
        name: str,
        args: int,
        kwargs: Set[str],
        starargs: bool,
        additional_kwargs: bool,
    ):
        self.name: str = name
        self.args: int = args
        self.kwargs: Set[str] = kwargs
        self.starargs: bool = starargs
        self.additional_kwargs: bool = additional_kwargs

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        items = ["*"] * self.args
        if self.starargs:
            items.append("...")
        items.extend([k + "=*" for k in sorted(self.kwargs)])
        if self.additional_kwargs:
            items.append("**")
        return f"{self.name}({','.join(items)})"

    def __repr__(self):
        return str(self)

    def match(self, func: Function, class_func=False) -> Tuple[bool, str]:
        """Check if this call matches the provided function signature

        Args:
            func (Function): The function signature

        Returns:
            Tuple[bool, str]: (match result, error message)
        """
        num_args = self.args if not class_func else self.args + 1

        matched_args = set()

        cand_posargs, posonly_args, cand_kwargs = [], [], set()
        allow_additional_kwargs = False
        allow_additional_posargs = False
        for arg in func.args:
            if not arg.kwarg and not arg.vararg and not arg.kw_only:
                cand_posargs.append(arg.name)
            if not arg.kwarg and not arg.vararg and not arg.pos_only:
                cand_kwargs.add(arg.name)
            if arg.pos_only:
                posonly_args.append(arg.name)
            if arg.vararg:
                allow_additional_posargs = True
            if arg.kwarg:
                allow_additional_kwargs = True

        if num_args > len(cand_posargs) and not allow_additional_posargs:
            return (
                False,
                f"{func.name}() takes up to {len(cand_posargs)} positional arguments but {num_args} are given",
            )
        matched_args.update(cand_posargs[:num_args])
        cand_kwargs = cand_kwargs - matched_args

        for kw in self.kwargs:
            if kw in posonly_args:
                return False, f"{kw} is position-only argument"
            if kw not in cand_kwargs and not allow_additional_kwargs:
                return False, f"{kw} is not allowed as keyword argument"
            matched_args.add(kw)

        for arg in func.args:
            if arg.kwarg or arg.vararg:
                continue
            if arg.default is None and arg.name not in matched_args:
                msg = f"{func.name}() missing one required argument {arg.name}"
                if not self.additional_kwargs and not self.starargs:
                    return (False, msg)
                elif arg.kw_only and not self.additional_kwargs:
                    return (False, msg)
                elif arg.pos_only and not self.starargs:
                    return (False, msg)

        return True, ""


class AccessChain(object):
    """An object representing an API access pattern

    It specifies certain constraints on an API access and can be used to match possible APIs
    For example: pandas.read_csv(*).head(*)

    Attributes:
        chain (List[Union[str, Call]]): The list of all accesses in this access chain
    """

    def __init__(self, chain: List[Union[str, Call]], line_nums: Set[int]):
        self.chain: List[Union[str, Call]] = chain
        self.line_nums: Set[int] = line_nums

    def __str__(self):
        return (
            ".".join(str(item) for item in self.chain)
            + ":"
            + ",".join(map(str, sorted(self.line_nums)))
        )

    def __repr__(self):
        return str(self)

    @property
    def top_level(self) -> str:
        return self.chain[0]

    @property
    def chain_str(self) -> str:
        return ".".join(str(item) for item in self.chain)

    def match(self, apis: Dict[str, Package]) -> MatchResult:
        if self.top_level not in apis:
            return MatchResult(MatchStatus.MISSING, f"{self.top_level} does not exist")

        curr_keys = []
        curr_chain = []
        curr_entity = apis[self.top_level]
        for i, item in enumerate(self.chain):
            name = item if isinstance(item, str) else item.name
            curr_keys.append(name)
            curr_chain.append(str(item))
            key = ".".join(curr_keys)
            chain = ".".join(curr_chain)

            try:
                curr_entity = apis[self.top_level].get(key)
            except KeyError:
                try:
                    curr_entity = apis[self.top_level][key]
                except KeyError:
                    return MatchResult(MatchStatus.MISSING, f"{key} does not exist")

            if isinstance(item, Call):
                if isinstance(curr_entity, Function):
                    match, message = item.match(curr_entity)
                    if not match:
                        return MatchResult(
                            MatchStatus.MISMATCH,
                            f"{chain} does not match function {curr_entity.signature}: {message}",
                        )
                elif isinstance(curr_entity, Class):
                    # If we can get class constructor, we check if the call matches it
                    # If we cannot, it means that the constructor is inherited,
                    #   and we know nothing about it, so we remain conseverative
                    if curr_entity.constructor is not None:
                        match, message = item.match(
                            curr_entity.constructor, class_func=True
                        )
                        if not match:
                            return MatchResult(
                                MatchStatus.MISMATCH,
                                f"{chain} does not match class constructor "
                                f"{curr_entity.constructor.signature}: {message}",
                            )
                    # We match class methods/properties if there is a subsequent method call
                    # We do not match properties because whether it match or not, we cannot know.
                    # Anything can be inherited from its parent class
                    if i < len(self.chain) - 1 and isinstance(self.chain[i + 1], Call):
                        method = curr_entity.get_method(self.chain[i + 1].name)
                        if method is not None:
                            static_method = any(
                                "staticmethod" in d for d in method.decorators
                            )
                            match, message = self.chain[i + 1].match(
                                method, class_func=not static_method
                            )
                            if match:
                                return MatchResult(
                                    MatchStatus.MATCH,
                                    "",
                                    ".".join(curr_keys) + "." + self.chain[i + 1].name,
                                    method,
                                )
                            else:
                                return MatchResult(
                                    MatchStatus.MISMATCH,
                                    f"{chain + '.' + str(self.chain[i + 1])} does not match class method "
                                    f"{method.signature}: {message}",
                                )

                elif isinstance(curr_entity, Package):
                    return MatchResult(
                        MatchStatus.MISMATCH,
                        f"{key} is a module but it is invoked",
                    )
                # If the entity is a variable or alias, we cannot know its real type, so be conservative
                break
            if not isinstance(curr_entity, Package):
                # The current chain accesses something, but we know nothing about it, so be conservative
                break

        return MatchResult(MatchStatus.MATCH, "", ".".join(curr_keys), curr_entity)
    

    @staticmethod
    def _from_str(chain_str: str, line_nums: Set[int] = None) -> AccessChain:
        chain = []
        for item in chain_str.split("."):
            if item.endswith(")"):
                name, argstrs = item.split("(")[0], item.split("(")[1][:-1]
                args, kwargs, additional_kwargs, starargs = 0, set(), False, False
                for argstr in argstrs.split(","):
                    if argstr == "":
                        continue
                    elif "=" in argstr:
                        kwargs.add(argstr.split("=")[0])
                    elif "**" in argstr:
                        additional_kwargs = True
                    elif "^^^" in argstr:
                        starargs = True
                    else:
                        args += 1
                chain.append(Call(name, args, kwargs, starargs, additional_kwargs))
            else:
                chain.append(item)
        return AccessChain(chain, line_nums)


class MatchStatus(Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    MISSING = "MISSING"


class MatchResult(object):
    def __init__(
        self,
        status: MatchStatus,
        message: str = "",
        matched_name: str = "",
        matched_api: Optional[Entity] = None,
    ):
        self.status: MatchStatus = status
        self.message: str = message
        self.matched_name: str = matched_name
        self.matched_api: Optional[Entity] = matched_api

    def __str__(self):
        if self.status == MatchStatus.MATCH:
            return (
                f"{self.status.value}: {self.matched_name} ({type(self.matched_api)})"
            )
        else:
            return f"{self.status.value}: {self.message}"

    def __repr__(self):
        return str(self)


def get_api_access_chains(
    code: str, module_filter: List[str] = None
) -> List[AccessChain]:
    """Extract API access chains from the source code of a .py file

    Args:
        code (str): The source code
        module_filter (List[str], optional): A list of module names. If not None, only
            access chains that begin with any of the provided module names will be retained.

    Returns:
        List[AccessChain]: A list of API access chains,
            guanranteed to be unique and sorted in alphabetical order
    """
    # Parse and build global context
    tree = ast.parse(code)
    visitor = _SourceVisitor()
    visitor.visit(tree)
    all_chains = _resolve_aliases(visitor.calls, visitor.aliases)
    api_access_chains = set()
    for chain, lineno in all_chains.items():
        if not any(chain.startswith(x) for x in visitor.imports):
            continue
        if module_filter is not None and not any(
            chain.startswith(x) for x in module_filter
        ):
            continue
        try:
            chain = AccessChain._from_str(chain, lineno)
        except IndexError:
            continue
        if any(
            isinstance(item, str) and not item.isidentifier() for item in chain.chain
        ):
            continue
        api_access_chains.add(chain)
    return list(sorted(api_access_chains, key=lambda x: str(x)))


def get_api_access_chains_from_folder(
    folder: str, module_filter: List[str] = None
) -> Dict[str, List[AccessChain]]:
    """Extract API access patterns from a Python project folder

    Args:
        folder (str): the path to project folder
        module_filter (List[str], optional): A list of module names. If not None, only
            access chains that begin with any of the provided module names will be retained.

    Returns:
        Dict[str, List[AccessChain]]: source file path -> list of API access chains
    """
    access_chains = {}
    for root, _, files in os.walk(folder):
        for f in files:
            if not f.endswith(".py"):
                continue
            file_path = os.path.join(root, f)
            try:
                with open(file_path, "r") as f:
                    code = f.read()
                access_chains[file_path] = get_api_access_chains(code, module_filter)
            except UnicodeDecodeError as ex:
                logger.warning(f"Unable to decode {f}: {ex}")
                continue
            except (SyntaxError, RecursionError) as ex:
                logger.warning(f"Unable to parse {f}: {ex}")
                continue
    return access_chains


def get_api_access_chains_from_wheel(
    wheel_path: str, module_filter: List[str] = None
) -> Dict[str, List[AccessChain]]:
    """Extract API access patterns from a Python package wheel (.whl) file

    Args:
        wheel_path (str): the path to wheel file
        module_filter (List[str], optional): A list of module names. If not None, only
            access chains that begin with any of the provided module names will be retained.

    Returns:
        Dict[str, List[AccessChain]]: source file path -> list of API access chains
    """
    access_chains = {}
    with open(wheel_path, "rb") as f:
        z = zipfile.ZipFile(f)
        for f in z.namelist():
            if not f.endswith(".py"):
                continue
            try:
                code = z.read(f).decode("utf-8", errors="ignore")
                access_chains[f] = get_api_access_chains(code, module_filter)
            except UnicodeDecodeError as ex:
                logger.warning(f"Unable to decode {f}: {ex}")
                continue
            except (SyntaxError, RecursionError) as ex:
                logger.warning(f"Unable to parse {f}: {ex}")
                continue
    return access_chains


class _SourceVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.imports: Set[str] = set()
        self.calls: Dict[str, Set[int]] = defaultdict(set)  # name -> line numbers
        self.aliases: Dict[str, Set[str]] = defaultdict(set)

    def visit_Import(self, node: ast.Import):
        for n in node.names:
            self.imports.add(n.name)
            if n.asname is None:
                self.calls[n.name].add(node.lineno)
            else:
                self.calls[n.asname].add(node.lineno)
                self.aliases[n.asname].add(n.name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module is None:
            return  # relative import, indicates internal module, skipping
        for n in node.names:
            self.imports.add(node.module + "." + n.name)
            if n.asname is None:
                self.calls[n.name].add(node.lineno)
                self.aliases[n.name].add(node.module + "." + n.name)
            else:
                self.calls[n.asname].add(node.lineno)
                self.aliases[n.asname].add(node.module + "." + n.name)

    def visit_Attribute(self, node: ast.Attribute):
        self.calls[self._parse_attribute(node)].add(node.lineno)

    def visit_Call(self, node: ast.Call):
        self.calls[self._parse_call(node)].add(node.lineno)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) == 0:
            self.aliases[self._parse(node.targets[0])].add(self._parse(node.value))
        else:
            self.aliases[self._parse(node.targets)].add(self._parse(node.value))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value is None:
            return
        self.aliases[self._parse(node.target)].add(self._parse(node.value))
        self.generic_visit(node)

    def _parse(self, node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return self._parse_attribute(node)
        elif isinstance(node, ast.Call):
            return self._parse_call(node)
        elif isinstance(node, ast.Name):
            return node.id
        return ast.unparse(node)

    def _parse_attribute(self, node: ast.Attribute) -> str:
        return self._parse(node.value) + "." + node.attr

    def _parse_call(self, node: ast.Call) -> str:
        items = ["*"] * len([n for n in node.args if not isinstance(n, ast.Starred)])
        if any(isinstance(n, ast.Starred) for n in node.args):
            items.append("^^^")
        items.extend([k.arg + "=*" for k in node.keywords if k.arg is not None])
        if any(k.arg is None for k in node.keywords):
            items.append("**")
        return f"{self._parse(node.func)}({','.join(items)})"


def _resolve_aliases(
    calls: Dict[str, Set[int]], aliases: Dict[str, Set[str]]
) -> Dict[str, Set[int]]:
    results = defaultdict(set, calls.items())
    prev_len = -1
    for _ in range(0, 5):
        if prev_len == len(results):
            break
        prev_len = len(results)
        for call, line_nums in list(results.items()):
            items = call.split(".")
            suffix = "." + ".".join(items[1:]) if len(items) > 1 else ""
            if items[0] in aliases:
                for alias in aliases[items[0]]:
                    if alias not in call:
                        results[alias + suffix].update(line_nums)
            elif items[0].endswith(")") and items[0].split("(")[0] in aliases:
                for alias in aliases[items[0].split("(")[0]]:
                    if alias not in call:
                        results[alias + "(" + items[0].split("(")[1] + suffix].update(
                            line_nums
                        )
            else:
                results[call].update(line_nums)
    return results
