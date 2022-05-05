"""Extract APIs using dynamic analysis"""

import os
import sys
import json
import logging
import inspect
import pkgutil
import traceback
import jsonpickle
import subprocess

from typing import Callable, List, Dict, Optional, Set, Tuple, Any, Union
from py4a.api.entity import Alias, Argument, Variable, Function, Class, Package


logger = logging.getLogger(__name__)


class PackageInstallException(Exception):
    pass


def _list_conda_envs() -> Set[str]:
    result = json.loads(
        subprocess.run(
            ["conda", "info", "--envs", "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.decode("utf-8", "ignore")
    )
    envs = set()
    for env in result["envs"]:
        for dir in result["envs_dirs"]:
            if env.startswith(dir):
                envs.add(os.path.relpath(env, dir))
    return envs


def _create_env(env_name: str, py_ver: str, packages: List[str] = []) -> bool:
    if env_name in _list_conda_envs():
        logger.info(f"Environment {env_name} already exists")
        return False
    subprocess.run(
        ["conda", "create", "-y", "--name", env_name, f"python={py_ver}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for pkg in packages + ["jsonpickle==2.0.0"]:
        try:
            result = subprocess.run(
                [
                    "conda",
                    "run",
                    "-n",
                    env_name,
                    "python",
                    "-m",
                    "pip",
                    "install",
                    pkg,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=900,
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout when installing {pkg} in {env_name}")
            return False
        if result.returncode != 0:
            logger.warning(f"Failed to install {pkg} for Python={py_ver}")
            return False
    return True


def _remove_env(env_name: str) -> bool:
    result = subprocess.run(
        ["conda", "remove", "-y", "--name", env_name, "--all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        logger.error(
            f"Failed to remove {env_name}: \n"
            + result.stdout.decode("utf-8", "ignore")
            + result.stderr.decode("utf-8", "ignore")
        )
        return False
    return True


def _get_type_name(obj: Any) -> str:
    if hasattr(obj, "__module__") and obj.__module__ == "typing":
        return str(obj)
    if not isinstance(obj, type):
        obj = type(obj)
    if hasattr(obj, "__qualname__"):
        name = obj.__qualname__
    elif hasattr(obj, "__name__"):
        name = obj.__name__
    else:
        name = str(obj)
    if hasattr(obj, "__module__") and obj.__module__ != "builtins":
        return str(obj.__module__) + "." + name
    else:
        return name


def _inspect_argument(name: str, param: inspect.Parameter) -> Argument:
    arg = Argument(name, None)
    if param.annotation != inspect.Parameter.empty:
        arg.type = _get_type_name(param.annotation)
    if param.default != inspect.Parameter.empty:
        arg.default = str(param.default)
    if param.kind == inspect.Parameter.POSITIONAL_ONLY:
        arg.pos_only = True
    elif param.kind == inspect.Parameter.KEYWORD_ONLY:
        arg.kw_only = True
    elif param.kind == inspect.Parameter.VAR_POSITIONAL:
        arg.vararg = True
    elif param.kind == inspect.Parameter.VAR_KEYWORD:
        arg.kwarg = True
    return arg


def _inspect_function(name: str, obj: Callable) -> Union[Function, Variable]:
    try:
        signature = inspect.signature(obj)
    except Exception:
        # It is possible some function cannot get signature
        # We just treat them as variables
        return Variable(name, _get_type_name(obj), str(obj))
    args, returns, is_async = [], None, False
    for param_name, param in signature.parameters.items():
        args.append(_inspect_argument(param_name, param))
    if signature.return_annotation != inspect.Signature.empty:
        returns = _get_type_name(signature.return_annotation)
    if inspect.iscoroutinefunction(obj):
        is_async = True
    # Decorators are always empty since they are only syntatic sugar
    return Function(name, args, returns, [], is_async)


def _inspect_class(name: str, cls: Any) -> Class:
    if hasattr(cls, "__bases__"):
        bases = [_get_type_name(base) for base in getattr(cls, "__bases__")]
    else:
        bases = []

    methods, static_fields, classes = [], [], []
    for member_name, member in inspect.getmembers(cls):
        if member_name.startswith("__") and member_name != "__init__":
            continue
        if inspect.isclass(member):
            classes.append(_inspect_class(member_name, member))
        elif inspect.isfunction(member) or callable(member):
            methods.append(_inspect_function(member_name, member))
        else:
            static_fields.append(
                Variable(
                    member_name,
                    _get_type_name(member),
                    str(getattr(cls, member_name, None)),
                )
            )

    # Class dynamic fields are not possible to infer without actually initializing one
    # So we resolve to a conservative way
    fields = []
    """
    for super in inspect.getmro(cls):
        try:
            tree = ast.parse(
                textwrap.dedent(inspect.getsource(super)), type_comments=True
            )
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                fields.extend(_convert_class_fields(node))
    """

    return Class(name, bases, fields, static_fields, methods, classes, [])


def get_apis_from_module(
    name: str, parent: Optional[Package] = None, failed_modules: Dict[str, str] = {}
) -> Package:
    package = Package(name, parent, {}, {})

    try:
        exec("import " + package.full_name)
    except Exception as e:
        logger.error(f"Failed to import {package.full_name}: {e}")
        failed_modules[package.full_name] = type(e).__name__ + ": " + str(e)
        return package

    module_obj = sys.modules[package.full_name]
    for attr_name, attr in inspect.getmembers(module_obj):
        if attr_name.startswith("__"):
            continue
        if inspect.ismodule(attr):
            module_name = attr.__name__.split(".")[-1]
            parent_module_name = ".".join(attr.__name__.split(".")[:-1])
            try:
                if parent_module_name == package.full_name:
                    package.children[attr_name] = get_apis_from_module(
                        module_name, package, failed_modules
                    )
                else:
                    package.entities[attr_name] = Alias(attr_name, attr.__name__)
            except Exception as ex:
                failed_modules[
                    package.full_name + "." + attr_name
                ] = f"Extraction failure due to {type(ex)}: {traceback.format_exc()}"
        elif inspect.isclass(attr):
            package.entities[attr_name] = _inspect_class(attr_name, attr)
        elif inspect.isfunction(attr) or callable(attr):
            package.entities[attr_name] = _inspect_function(attr_name, attr)
        else:
            package.entities[attr_name] = Variable(
                attr_name, _get_type_name(attr), str(attr)
            )

    """
    # A child module may not have been imported, so we need to check using pkgutil
    if module_obj.__file__.endswith("__init__.py"): # is a folder
        for _, name, _ in pkgutil.iter_modules(module_obj.__path__):
            if name in package.children:
                continue
            try:
                package.children[name] = get_apis_from_module(
                    name, package, failed_modules
                )
            except Exception as ex:
                failed_modules[
                    package.full_name + "." + name
                ] = f"Extraction failure due to {type(ex)}: {traceback.format_exc()}"
    """
    return package


def get_apis_from_runtime(
    pkg_name: str, ver: str, top_levels: List[str]
) -> Tuple[Dict[str, Package], Dict[str, str]]:
    if pkg_name == "jsonpickle":
        raise ValueError(
            "jsonpickle is used during dynamic analysis and thus not supported"
        )

    conda_env = f"{pkg_name}-{ver}"
    candidate_py_vers = ["3.9", "3.8", "3.7", "3.6"]
    successful = False
    for py_ver in candidate_py_vers:
        if conda_env in _list_conda_envs():
            _remove_env(conda_env)
        if _create_env(conda_env, py_ver, [f"{pkg_name}=={ver}"]):
            successful = True
            break
    if not successful:
        if conda_env in _list_conda_envs():
            _remove_env(conda_env)
        raise PackageInstallException(
            f"Fail to install {pkg_name}=={ver} in a conda env with Python>=3.6"
        )

    try:
        apis, failed_modules = {}, {}
        for top_level in top_levels:
            result = subprocess.run(
                ["conda", "run", "-n", conda_env, "python", "-m", __name__, top_level],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3600,
            )
            if result.returncode != 0:
                failed_modules[top_level] = result.stderr.decode("utf-8", "ignore")
                continue
            result = jsonpickle.loads(result.stdout.decode("utf-8", "ignore"))
            apis[top_level] = result["apis"]
            failed_modules.update(result["failed_modules"])
    finally:
        _remove_env(conda_env)
    return apis, failed_modules


if __name__ == "__main__":
    top_level = sys.argv[1]
    failed_modules = {}
    apis = get_apis_from_module(top_level, None, failed_modules)
    print(jsonpickle.dumps({"apis": apis, "failed_modules": failed_modules}))
