"""Extract API entities from Python source code"""

# from __future__ import annotations # Need Python 3.7

import os
import ast
import textwrap
import jsonpickle

from copy import deepcopy
from typing import List, Dict, Optional


class Entity(object):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name

    @property
    def signature(self) -> str:
        return self.name

    def __str__(self):
        return jsonpickle.encode(self, indent=2)

    def __repr__(self):
        return str(self)

    @staticmethod
    def decode(s: str) -> "Entity":
        return jsonpickle.decode(s)

    @staticmethod
    def decode_f(path: str) -> "Entity":
        if not os.path.isfile(path):
            raise ValueError(f"{path} does not exist in file system")
        with open(path, "r") as f:
            s = f.read()
        return jsonpickle.decode(s)


class Argument(Entity):
    def __init__(
        self,
        name: str,
        type: Optional[str],
        default: Optional[str] = None,
        pos_only: bool = False,
        kw_only: bool = False,
        vararg: bool = False,
        kwarg: bool = False,
    ) -> None:
        super().__init__(name)
        self.type: Optional[str] = type
        self.default: Optional[str] = default
        self.pos_only: bool = pos_only
        self.kw_only: bool = kw_only
        self.vararg: bool = vararg
        self.kwarg: bool = kwarg

    @property
    def eval_default(self):
        return ast.literal_eval(self.default)


class Function(Entity):
    def __init__(
        self,
        name: str,
        args: List[Argument],
        returns: Optional[str],
        decorators: List[str],
        is_async: bool,
    ) -> None:
        super().__init__(name)
        self.args: List[Argument] = args
        self.returns: Optional[str] = returns
        self.decorators: List[str] = decorators
        self.is_async: bool = is_async

    @property
    def signature(self) -> str:
        items = []
        for i, arg in enumerate(self.args):
            if i >= 1 and self.args[i - 1].pos_only and not arg.pos_only:
                items.append("/")
            base = arg.name + (f": {arg.type}" if arg.type is not None else "")
            if arg.vararg:
                base = "*" + base
            if arg.kwarg:
                base = "**" + base
            if arg.default is not None:
                base += f" = {arg.default}"
            items.append(base)
        s = f"def {self.name}({', '.join(items)})"
        for decorator in reversed(self.decorators):
            s = f"@{decorator} {s}"
        if self.is_async:
            s = "async " + s
        if self.returns is not None:
            s = s + " -> " + self.returns
        return s

    def get_arg(self, name: str) -> Optional[Argument]:
        for arg in self.args:
            if arg.name == name:
                return arg
        raise None


class Variable(Entity):
    def __init__(self, name: str, type: str, value: str) -> None:
        super().__init__(name)
        self.type: str = type
        self.value: str = value

    @property
    def eval_value(self):
        return ast.literal_eval(self.value)

    @property
    def signature(self) -> str:
        if self.type != "":
            return f"{self.name} : {self.type} = {self.value}"
        else:
            return f"{self.name} = {self.value}"


class Class(Entity):
    def __init__(
        self,
        name: str,
        bases: List[str],
        fields: List[Variable],
        static_fields: List[Variable],
        methods: List[Function],
        classes: List["Class"],
        decorators: List[str],
    ) -> None:
        super().__init__(name)
        self.bases: List[str] = bases
        self.fields: List[Variable] = fields
        self.static_fields: List[Variable] = static_fields
        self.methods: List[Function] = methods
        self.classes: List[Class] = classes
        self.decorators: List[str] = decorators

    @property
    def constructor(self) -> Optional[Function]:
        for m in self.methods:
            if m.name == "__init__":
                return m
        return None

    @property
    def signature(self) -> str:
        s = f"class {self.name}({','.join(self.bases)}):\n"
        for static_field in self.static_fields:
            s += f"    (static) {static_field.signature}\n"
        for field in self.fields:
            s += f"    {field.signature}\n"
        for method in self.methods:
            s += f"    {method.signature}\n"
        for class_ in self.classes:
            s += "\n".join("    " + l for l in class_.signature.splitlines())
        return s

    def get_field(self, name: str) -> Optional[Variable]:
        for m in self.fields:
            if m.name == name:
                return m
        return None

    def get_static_field(self, name: str) -> Optional[Variable]:
        for m in self.static_fields:
            if m.name == name:
                return m
        return None

    def get_method(self, name: str) -> Optional[Function]:
        for m in self.methods:
            if m.name == name:
                return m
        return None

    def get_class(self, name: str) -> Optional["Class"]:
        for m in self.classes:
            if m.name == name:
                return m
        return None

    def get_entity(self, name: str) -> Optional[Entity]:
        if "." not in name:
            for m in self.methods + self.fields + self.static_fields:
                if m.name == name:
                    return m
        else:
            prefix, suffix = name.split(".", 1)
            for m in self.classes:
                if m.name == prefix:
                    return m.get_entity(suffix)
        return None

    def get_names(self) -> List[str]:
        names = []
        names.extend([m.name for m in self.methods])
        names.extend([f.name for f in self.fields])
        names.extend([f.name for f in self.static_fields])
        for c in self.classes:
            names.append(c.name)
            names.extend([c.name + n for n in c.get_names()])
        return names


class Package(Entity):
    """The class used to represent all API entities in a Python package."""

    def __init__(
        self,
        name: str,
        parent: "Package",
        children: Dict[str, "Package"],
        entities: Dict[str, Entity],
    ):
        super().__init__(name)
        self.parent: Package = parent
        self.children: Dict[str, Package] = children
        self.entities: Dict[str, Entity] = entities

    @property
    def signature(self) -> str:
        s = f"Package {self.name}:"
        if len(self.children) > 0:
            s += f"\nChildren: \n"
            s += textwrap.indent(
                "\n".join(c.full_name for c in self.children.values()), "    "
            )
        if len(self.entities) > 0:
            s += f"\nEntities: \n"
            s += textwrap.indent(
                "\n".join(e.signature for e in self.entities.values()), "    "
            )
        return s

    @property
    def full_name(self) -> str:
        """The full name of this package, including all parent packages.

        For example, the package name is "foo" and is the subpackage of "bar",
            the full name will be "bar.foo".

        Returns:
            str: the full name
        """
        full_name = self.name
        curr = self.parent
        while curr is not None:
            full_name = curr.name + "." + full_name
            curr = curr.parent
        return full_name

    def get(
        self,
        key: str,
        top_levels: Dict[str, "Package"] = {},
        prev_aliases: List[str] = [],
    ) -> Entity:
        """Find the actual API entity.

        It will search over aliases and wildcard imports (depth first search) within this package,
            to find the actual referred API entity (Function, Class, or Variable)

        Args:
            key (str): The API entity name.
            top_levels (Dict[str, Package]): The top level packages to resolve aliases.
            prev_aliases (List[str], optional): Stores previously resolved names.
                Used to detect cyclic aliases which may occur in buggy code. Defaults to [].

        Raises:
            KeyError: If API entity name does not exist in this package,
                or there is a cyclic reference,
                or the API entity is an alias that points to an external module.

        Returns:
            Entity: An API entity.
        """
        res = self[key]
        if isinstance(res, (Alias, WildcardAlias)):
            aliases = [res.full_alias] if isinstance(res, Alias) else res.full_aliases
            for alias in aliases:
                if alias in prev_aliases:
                    raise KeyError(f"{key} is a cyclic reference")
                top_level = alias.split(".")[0]
                try:
                    if top_level == self.name:
                        return self.get(alias, top_levels, prev_aliases + [alias])
                    elif top_level in top_levels:
                        return top_levels[top_level].get(
                            alias, top_levels, prev_aliases + [alias]
                        )
                except KeyError:
                    continue
            raise KeyError(f"{key} cannot be resolved in this package")
        return res

    def query(
        self,
        key: str,
        top_levels: Dict[str, "Package"] = None,
        prev_aliases: List[str] = [],
    ) -> Entity:
        """An alternative version of get()"""
        if top_levels is None:
            top_levels = {self.name: self}

        items = key.split(".")
        if items[0] != self.name:
            raise KeyError(f"{key} is not in this package")
        if len(items) == 1:
            return self

        first, next = items[1], ".".join(items[2:]) if len(items) > 2 else None
        if first in self.children:
            res = self.children[first]
        elif first in self.entities:
            res = self.entities[first]
        else:
            res = None

        if isinstance(res, Alias) or (res is None and "*" in self.entities):
            if isinstance(res, Alias):
                aliases = [res.full_alias]
            else:
                aliases = []
                for wildcard in self.entities["*"].full_aliases:
                    aliases.append(wildcard.replace("*", first))
            for alias in aliases:
                if alias in prev_aliases:
                    raise KeyError(f"{key} is a cyclic reference")
                top_level = alias.split(".")[0]
                next_name = alias if next is None else alias + "." + next
                try:
                    # if top_level == self.name:
                    # return self.get(next_name, top_levels, prev_aliases + [alias])
                    # elif top_level in top_levels:
                    return top_levels[top_level].query(
                        next_name, top_levels, prev_aliases + [alias]
                    )
                except KeyError:
                    continue
            raise KeyError(f"{key} cannot be resolved in this package")

        if res is None and "*" not in self.entities:
            raise KeyError(f"{key} is not in this package")
        if next is None:
            return res
        elif isinstance(res, Class):
            return res.get_entity(next)
        elif isinstance(res, Package):
            return res.query(first + "." + next, top_levels, prev_aliases)
        else:
            raise KeyError(f"{key} is not in this package")

    def keys(self, leaf_only=True) -> List[str]:
        """Get a list of API entity names in this package.

        Args:
            leaf_only (bool, optional): Whether to only include leaf nodes (API entities).
                Defaults to True.

        Returns:
            List[str]: A list of API entity names for accessing elements in this Package
        """
        result = [] if leaf_only else [self.full_name]
        for k in self.entities:
            result.append(self.full_name + "." + k)
        for child in self.children:
            result += self.children[child].keys(leaf_only)
        return result

    def modules(self) -> List[str]:
        """Get a list of all module names in this package

        Returns:
            List[str]: A list of module names
        """
        result = [self.full_name]
        for child in self.children:
            result += self.children[child].modules()
        return result

    def __getitem__(self, key: str) -> Entity:
        """Access API Entities in this package.

        Supports patterns like "foo.bar.func" for accessing sub-modules/packages.
        `__getitem__()` does not resolve any aliases. Use `get()` for that purpose.

        Args:
            key (str): The API enitity name (e.g., "foo.bar.func1").

        Returns:
            Entity: An API entity.
        """
        keys = key.split(".")
        if keys[0] != self.name:
            raise KeyError(f"{key} does not belong to this package")
        res = self

        for i, k in enumerate(keys[1:]):
            if isinstance(res, Package):
                if k in res.children:
                    res = res.children[k]
                elif k in res.entities:
                    res = res.entities[k]
                elif "*" in res.entities and i == len(keys[1:]) - 1:
                    res = deepcopy(res.entities["*"])
                    res.name = res.name.replace("*", k)
                    res.full_aliases = [x.replace("*", k) for x in res.full_aliases]
                else:
                    raise KeyError(f"{key} does not correspond to an API entity")
            else:
                raise KeyError(f"{key} does not correspond to an API entity")
        return res

    def __contains__(self, key: str) -> bool:
        """Test whether an API entity exist in this package.

        NOTE: If a package (say `foo.bar`) contains statements like `from abc import *`,
            tests like `foo.bar.xxx` will always return True due to this wildcard import,
            even if API `foo.bar.xxx` may not actually exist.

        Args:
            key (str): the API entity name (e.g., "foo.bar.func1").

        Returns:
            bool: whether the API entity exists
        """
        try:
            self[key]
            return True
        except KeyError:
            return False


class Alias(Entity):
    def __init__(self, name: str, full_alias: str):
        super().__init__(name)
        self.full_alias: str = full_alias

    @property
    def signature(self) -> str:
        return super().signature + f" -> {self.full_alias}"


class WildcardAlias(Entity):
    def __init__(self, full_aliases: List[str]):
        super().__init__("*")
        self.full_aliases: List[str] = full_aliases

    @property
    def signature(self) -> str:
        return super().signature + f" -> {self.full_aliases}"
