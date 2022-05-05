import py4a.api.entity as entity
import py4a.api.dynamic as dynamic

from typing import Any, Type, Dict


def test_conda():
    if "test_conda" in dynamic._list_conda_envs():
        dynamic._remove_env("test_conda")
    assert dynamic._create_env("test_conda", "3.6", ["pandas==1.0.0"])
    assert "test_conda" in dynamic._list_conda_envs()
    assert dynamic._remove_env("test_conda")
    assert "test_conda" not in dynamic._list_conda_envs()


def test_get_type_name():
    assert dynamic._get_type_name(1) == "int"
    assert dynamic._get_type_name(int) == "int"
    assert dynamic._get_type_name(A) == "test_dynamic.A"
    assert dynamic._get_type_name(A.Inner) == "test_dynamic.A.Inner"
    assert dynamic._get_type_name(entity.Entity) == "py4a.api.entity.Entity"
    assert dynamic._get_type_name(Dict) == "typing.Dict"


def f1(a: int = 1, b: str = "2") -> int:
    return a + int(b)


async def f2(a: Any, /, b=1, c=2, *d, e: Type, f=2, **g) -> Dict:
    pass


class A(object):
    A = 1
    B: str = "abc"

    def __init__(self, a: int = 1, b: str = "2"):
        self.a = a
        self.b = b

    def f(self, c: int = 3) -> str:
        return A + self.b + self.c

    class Inner:
        def __init__(self, i: int = 1):
            self.i = i


def test_inspect_function():
    func = dynamic._inspect_function("f1", f1)
    print(func.signature)
    assert func.name == "f1"
    assert not func.is_async
    assert func.get_arg("a").default == "1"
    assert func.returns == "int"

    func = dynamic._inspect_function("f2", f2)
    print(func.signature)
    assert func.name == "f2"
    assert func.is_async
    assert func.get_arg("a").default is None
    assert func.get_arg("a").pos_only
    assert func.get_arg("b").default == "1"
    assert func.get_arg("e").kw_only
    assert func.get_arg("g").kwarg


def test_inspect_class():
    cls = dynamic._inspect_class("A", A)
    print(cls.signature)
    assert cls.get_method("f").get_arg("c").default == "3"
    assert cls.get_method("f").returns == "str"
    assert cls.get_method("__init__").get_arg("a").type == "int"
    assert cls.get_static_field("A").type == "int"
    assert cls.get_static_field("B").value == "abc"
    assert cls.get_class("Inner").get_method("__init__").get_arg("i").type == "int"
    # assert cls.get_field("a") is not None
    # assert cls.get_field("b") is not None


def test_get_apis_from_module():
    failed = {}
    pkg = dynamic.get_apis_from_module("tests.api.test_dynamic", None, failed)
    print(pkg.signature)
    print(failed)
    assert "test_get_apis_from_module" in pkg.entities
    assert len(failed) == 0

    pkg = dynamic.get_apis_from_module("py4a", None, failed)
    print(pkg.signature)
    print(pkg.children["check_pypi_dep_error"].signature)
    print(pkg.get("py4a.api.entity").signature)
    print(failed)
    assert len(failed) == 0

    pkg = dynamic.get_apis_from_module("os", None, failed)
    print(pkg.signature)
    print(failed)
    assert len(failed) == 0


def test_get_apis():
    vers = ["0.25.2", "1.0.0"]
    for ver in vers:
        pkg, failed = dynamic.get_apis_from_runtime("pandas", ver, ["pandas"])
        print(pkg["pandas"].signature)
        print(pkg["pandas"].get("pandas.read_csv").signature)
        print(failed)
        # assert len(failed) == 0


def test_get_apis2():
    pkg, failed = dynamic.get_apis_from_runtime("nbclassic", "0.3.4", ["nbclassic"])
    print(pkg["nbclassic"].signature, failed.keys())
    # assert pkg["nbclassic"]["nbclassic.shim"]
    # assert "nbclassic.conftest" in failed
