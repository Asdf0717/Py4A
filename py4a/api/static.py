"""Extract APIs using static analysis"""
import os
import ast
import shutil
import logging

from typing import List, Union
from copy import deepcopy
from zipfile import ZipFile
from wheel_inspect import inspect_wheel
from py4a.api.entity import *


logger = logging.getLogger(__name__)
failed_modules = {}  # This variable is not thread safe


def _normalize_failed_modules(base_path: str):
    global failed_modules
    base_path = os.path.abspath(base_path)
    for path in list(failed_modules.keys()):
        rel_path = os.path.relpath(path, base_path)
        if rel_path.endswith(".py"):
            rel_path = rel_path[:-3]
        elif rel_path.endswith(".pyi"):
            rel_path = rel_path[:-4]
        rel_path = rel_path.replace(os.sep, ".")
        failed_modules[rel_path] = failed_modules[path]
        del failed_modules[path]


def get_api_entities(tree: ast.AST) -> List[Entity]:
    """Extracts API entities from a Python AST (assuming from a source file).

    Args:
        tree (ast.AST): AST representation of a Python module (i.e., .py file).

    Returns:
        List[Entity]: the list of API entities defined in this file.
    """
    visitor = _SourceVisitor()
    visitor.visit(tree)
    return visitor.api_entities


def get_apis_from_wheel(name: str, wheel_path: str) -> List[Package]:
    """Extract package API entities from a wheel.

    Args:
        name (str): Name of the package
        wheel_path (str): Path to wheel

    Returns:
        List[Package]: The extracted API entities,
            may be more than one package if the wheel has more than one top levels
    """
    global failed_modules

    if not wheel_path.endswith(".whl") or not os.path.isfile(wheel_path):
        raise ValueError(f"Wheel file does not exist or not .whl: {wheel_path}")
    extract_dir = wheel_path.replace(".whl", "")
    if os.path.exists(extract_dir):
        logger.warning(f"{extract_dir} already exists")
        shutil.rmtree(extract_dir)

    failed_modules = {}
    packages = []
    try:
        with ZipFile(wheel_path, "r") as zip_archive:
            zip_archive.extractall(extract_dir)

        wheel_metadata = inspect_wheel(wheel_path)
        top_levels = [name]
        if "top_level" in wheel_metadata["dist_info"]:
            top_levels = wheel_metadata["dist_info"]["top_level"]

        for top_level in top_levels:
            pkg_path = os.path.join(extract_dir, top_level)
            if os.path.isdir(pkg_path):
                entries = _get_entry_points(pkg_path)
                package = _get_apis(top_level, pkg_path, entries)
                _resolve_import_from(package)
                packages.append(package)
            elif os.path.isfile(pkg_path + ".py"):  # Single file package
                entities = _get_apis_from_source(pkg_path + ".py")
                if os.path.isfile(pkg_path + ".pyi"):
                    entities += _get_apis_from_source(pkg_path + ".pyi")
                package = Package(top_level, None, {}, entities)
                _resolve_import_from(package)
                packages.append(package)
            elif os.path.isfile(
                pkg_path + ".pyi"
            ):  # In this case, the .py file does not exist
                # Sometimes the source code is implemented in C
                #    while a .pyi is provided in Python.
                # In this case, we extract APIs from corresponding .pyi file.
                entities = _get_apis_from_source(pkg_path + ".pyi")
                package = Package(top_level, None, {}, entities)
                _resolve_import_from(package)
                packages.append(package)
            else:
                logger.error(f"{top_level} does not exist for wheel {wheel_path}")
    finally:
        _normalize_failed_modules(extract_dir)
        shutil.rmtree(extract_dir)
    return packages


def get_apis_from_dir(name: str, dir: str) -> Package:
    """Extract all APIs from a directory containing a Python package

    Args:
        name (str): Name of the package
        dir (str): The directory to analyze

    Returns:
        Package: The extracted APIs
    """
    global failed_modules
    failed_modules = {}
    entries = _get_entry_points(dir)
    package = _get_apis(name, dir, entries)
    _resolve_import_from(package)
    _normalize_failed_modules(dir)
    return package


def get_apis_from_file(name: str, dir: str) -> Package:
    """Extract all APIs from a file containing a Python package

    Args:
        name (str): Name of the package
        dir (str): The path to the file to analyze

    Returns:
        Package: The extracted APIs
    """
    global failed_modules
    failed_modules = {}
    entities = _get_apis_from_source(dir)
    package = Package(name, None, {}, entities)
    _resolve_import_from(package)
    return package


class _SourceVisitor(ast.NodeVisitor):
    def __init__(self):
        self.api_entities: List[Entity] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.api_entities.append(_convert_function(node))
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        self.api_entities.append(_convert_class(node))
        return node

    def visit_Assign(self, node: ast.Assign):
        self.api_entities.extend(_convert_variables(node))
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.api_entities.extend(_convert_variables(node))
        return node


def _convert_arguments(arguments: ast.arguments) -> List[Argument]:
    results = []
    default_starts = (
        len(arguments.posonlyargs) + len(arguments.args) - len(arguments.defaults)
    )
    arg_type = lambda arg: ast.unparse(arg.annotation) if arg.annotation else None

    for i, arg in enumerate(arguments.posonlyargs + arguments.args):
        if i >= default_starts:
            default = arguments.defaults[i - default_starts]
            default = ast.unparse(default)
        else:
            default = None
        results.append(
            Argument(
                name=arg.arg,
                type=arg_type(arg),
                default=default,
                pos_only=True if i < len(arguments.posonlyargs) else False,
            )
        )

    if arguments.vararg:
        results.append(
            Argument(
                name=arguments.vararg.arg,
                type=arg_type(arguments.vararg),
                vararg=True,
            )
        )

    for i, arg in enumerate(arguments.kwonlyargs):
        default = arguments.kw_defaults[i]
        default = ast.unparse(default) if default is not None else None
        results.append(
            Argument(name=arg.arg, type=arg_type(arg), default=default, kw_only=True)
        )

    if arguments.kwarg:
        results.append(
            Argument(
                name=arguments.kwarg.arg,
                type=arg_type(arguments.kwarg),
                kwarg=True,
            )
        )

    return results


def _convert_variables(assign: Union[ast.Assign, ast.AnnAssign]) -> List[Variable]:
    results = []
    if assign.value is None:
        return results
    targets = assign.targets if isinstance(assign, ast.Assign) else [assign.target]
    t = ast.unparse(assign.annotation) if isinstance(assign, ast.AnnAssign) else None
    for target in targets:
        if isinstance(target, ast.Name):
            v = ast.unparse(assign.value) if assign.value else None
            results.append(Variable(target.id, t, v))
        elif isinstance(target, ast.Tuple):
            for i, elt in enumerate(target.elts):
                if isinstance(elt, ast.Name):
                    if isinstance(assign.value, (ast.Tuple, ast.List)):
                        v = ast.unparse(assign.value.elts[i])
                    else:
                        v = ast.unparse(assign.value) + "[" + str(i) + "]"
                    results.append(Variable(elt.id, None, v))
        # Ignore ast.Attribute
    return results


def _convert_function(func: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Function:
    return Function(
        name=func.name,
        args=_convert_arguments(func.args),
        returns=ast.unparse(func.returns) if func.returns else None,
        decorators=[ast.unparse(d) for d in func.decorator_list],
        is_async=isinstance(func, ast.AsyncFunctionDef),
    )


def _convert_class_fields(assign: Union[ast.Assign, ast.AnnAssign]) -> List[Variable]:
    results = []
    if assign.value is None:
        return results
    targets = assign.targets if isinstance(assign, ast.Assign) else [assign.target]
    t = ast.unparse(assign.annotation) if isinstance(assign, ast.AnnAssign) else None
    is_field = (
        lambda target: isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    )
    for target in targets:
        if is_field(target):
            v = ast.unparse(assign.value) if assign.value else None
            results.append(Variable(target.attr, t, v))
        elif isinstance(target, ast.Tuple):
            for i, elt in enumerate(target.elts):
                if is_field(elt):
                    if isinstance(assign.value, (ast.Tuple, ast.List)):
                        v = ast.unparse(assign.value.elts[i])
                    else:
                        v = ast.unparse(assign.value) + "[" + str(i) + "]"
                    results.append(Variable(elt.attr, None, v))
    return results


def _convert_class(cls: ast.ClassDef) -> Class:
    methods = []
    fields = []
    static_fields = []
    classes = []
    for node in cls.body:
        if isinstance(node, ast.FunctionDef):
            methods.append(_convert_function(node))
            if node.name == "__init__":
                for node2 in ast.walk(node):
                    if isinstance(node2, (ast.Assign, ast.AnnAssign)):
                        fields.extend(_convert_class_fields(node2))
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            static_fields.extend(_convert_variables(node))
        if isinstance(node, ast.ClassDef):
            classes.append(_convert_class(node))
    return Class(
        name=cls.name,
        bases=[ast.unparse(b) for b in cls.bases],
        methods=methods,
        fields=fields,
        static_fields=static_fields,
        classes=classes,
        decorators=[ast.unparse(d) for d in cls.decorator_list],
    )


def _get_apis_from_source(path: str) -> List[Entity]:
    """Extract all APIs from a source file (i.e., `.py` file or `.pyi` file).

    Args:
        path (str): The path to source file.

    Returns:
        List[Entity]: A list of extracted API entites.
    """
    global failed_modules
    entities = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), type_comments=True)
        entities.extend(get_api_entities(tree))
        for n in ast.walk(tree):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                entities.append(n)
    except (SyntaxError, RecursionError) as ex:
        logger.error(f"{path} has syntax error: {ex}")
        failed_modules[os.path.abspath(path)] = f"{type(ex)}: {ex}"
    return entities


def _get_apis(
    name: str, dir: str, entry_points: List[str], parent: Package = None
) -> Package:
    """Extract all APIs from a directory containing a Python package

    Note: Alias resolution is not done in this function.

    Args:
        name (str): Name of the package
        dir (str): The directory to analyze
        entry_points (List[str]): Package entry points,
            can be either provided by Wheel metadata or inferred from files
        parent (Package, optional): The parent package. Defaults to None.

    Raises:
        FileNotFoundError: If the directory does not exist
        ValueError: If the provided entry points does not exist or have unsupported file suffix

    Returns:
        Package: The extracted APIs without alias resolution
    """
    if not os.path.isdir(dir):
        raise FileNotFoundError(f"{dir} must be a directory")
    package = Package(name, parent, {}, {})
    for entry in entry_points:
        entry_path = os.path.join(dir, entry)
        if os.path.isdir(entry_path):
            next_entry_points = _get_entry_points(entry_path)
            package.children[entry] = _get_apis(
                entry, entry_path, next_entry_points, package
            )
        elif os.path.isfile(entry_path + ".py"):
            entities = _get_apis_from_source(entry_path + ".py")
            if os.path.isfile(entry_path + ".pyi"):
                entities += _get_apis_from_source(entry_path + ".pyi")
            package.children[entry] = Package(entry, package, {}, entities)
        elif os.path.isfile(entry_path + ".pyi"):
            # Sometimes the source code is implemented in C
            #    while a .pyi is provided in Python.
            # In this case, we extract APIs from corresponding .pyi file.
            entities = _get_apis_from_source(entry_path + ".pyi")
            package.children[entry] = Package(entry, package, {}, entities)
        else:
            raise ValueError(f"Entry does not exist or not supported: {entry_path}")
    return package


def _get_entry_points(dir: str) -> List[str]:
    """Infer entry points from a directory containing a Python package.

    Note: The results may be inaccurate, so this function should not be used
      if the Python wheel metadata already provides accurate entry points.

    Args:
        dir (str): The directory

    Raises:
        FileNotFoundError: if the directory does not exist
    Returns:
        List[str]: A list of entry points
    """
    if not os.path.isdir(dir):
        raise FileNotFoundError(f"{dir} must be a directory")
    # if not os.path.isfile(os.path.join(dir, "__init__.py")):
    #     raise FileNotFoundError(f"{dir} does not look like a package (no __init__.py)")
    entry_points = []
    for child in os.listdir(dir):
        # if child.startswith("test"):
        #    continue  # A heuristic to ignore test code if any
        next_dir = os.path.join(dir, child)
        if os.path.isdir(next_dir) and os.path.isfile(
            os.path.join(next_dir, "__init__.py")
        ):
            entry_points.append(child)
        elif next_dir.endswith(".py") and not next_dir.endswith("setup.py"):
            entry_points.append(child[:-3])  # Remove .py suffix
        elif next_dir.endswith(".pyi") and child[:-4] not in entry_points:
            entry_points.append(child[:-4])  # Remove .pyi suffix
    return entry_points


def _resolve_import_from(package: Package):
    """Resolve all ast.ImportFrom statements into API aliases"""
    for subpackage in package.children.values():
        _resolve_import_from(subpackage)
    new_entities = [
        e for e in package.entities if not isinstance(e, (ast.Import, ast.ImportFrom))
    ]
    wildcard_alias = WildcardAlias([])
    for entity in package.entities:
        if isinstance(entity, ast.Import):
            for name in entity.names:
                new_entities.append(
                    Alias((name.asname if name.asname else name.name), name.name)
                )
        elif isinstance(entity, ast.ImportFrom):
            if entity.level == 0:  # absolute import
                full_module_name = entity.module
            else:  # relative import
                if entity.level == 1:
                    full_module_name = package.parent.full_name + (
                        ("." + entity.module) if entity.module is not None else ""
                    )
                else:
                    full_module_name = ".".join(
                        package.parent.full_name.split(".")[: -entity.level + 1]
                        + ([entity.module] if entity.module is not None else [])
                    )
            for name in entity.names:
                full_alias = full_module_name + "." + name.name
                if name.name == "*":
                    wildcard_alias.full_aliases.append(full_alias)
                    continue
                new_entities.append(
                    Alias((name.asname if name.asname else name.name), full_alias)
                )
    if len(wildcard_alias.full_aliases) > 0:
        new_entities.append(wildcard_alias)
    package.entities = {}
    for e in new_entities:
        if e.name not in package.entities:
            package.entities[e.name] = e
    if "__init__" in package.children:
        package.entities = deepcopy(package.children["__init__"].entities)
