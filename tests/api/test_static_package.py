import ast
import pathlib
import py4a.api.static as static

from py4a.api.entity import Alias, Function, Variable, Function, Package


def test_get_apis_from_wheel():
    pathlib.Path("temp").mkdir(exist_ok=True)

    packages = static.get_apis_from_wheel(
        "six", "tests/resource/six-1.16.0-py2.py3-none-any.whl"
    )
    with open("temp/six.json", "w") as f:
        f.write(str(packages))
    assert packages[0]["six.__version__"].eval_value == "1.16.0"

    packages = static.get_apis_from_wheel(
        "pandas",
        "tests/resource/pandas-1.3.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    )
    with open("temp/pandas.json", "w") as f:
        f.write(str(packages))
    assert isinstance(packages[0]["pandas.read_excel"], Alias)
    assert isinstance(packages[0].get("pandas.read_excel"), Function)
    assert packages[0]["pandas.core.dtypes"]
    assert packages[0]["pandas.core.dtypes.dtypes"]
    assert packages[0]["pandas.core.dtypes.dtypes.ExtensionDtype"]


def test_get_apis_from_dir():
    package = static.get_apis_from_dir("simple", "tests/resource/package-simple/simple")
    print(package)
    assert package["simple.func2"].full_alias == "simple.lib2.func2"
    assert package["simple.f3"].full_alias == "simple.lib3.func3"
    assert len(package.entities) == 5
    assert "simple.path" in package and "simple.os" in package
    assert all(k in package.keys() for k in ["simple.f3", "simple.lib2.func2"])
    assert package["simple.m1.func2"].name == "func2"
    assert isinstance(package["simple.f3"], Alias) and isinstance(
        package["simple.func2"], Alias
    )
    assert package["simple.*"].full_aliases == ["simple.lib3.*", "sys.*"]
    assert isinstance(package.get("simple.func3"), Function)


def test_get_apis():
    entries = static._get_entry_points("tests/resource/package-simple/")
    print(entries)
    package = static._get_apis(
        "package-simple", "tests/resource/package-simple/", entries
    )
    print(package)
    assert package.name == "package-simple" and package.parent is None
    assert (
        package.children["lib1"].entities[0].name == "__ver__"
        and ast.literal_eval(package.children["lib1"].entities[0].value) == "1.0.0"
    )
    assert (
        package.children["simple"].parent == package
        and package.children["simple"].children["lib2"].entities[0].name == "func2"
        and package.children["simple"].children["lib3"].entities[0].name == "func3"
    )


def test_get_entry_points():
    entries = static._get_entry_points("tests/resource/package-simple/")
    assert "lib1" in entries and "setup" not in entries and "simple" in entries
    entries = static._get_entry_points("tests/resource/package-simple/simple")
    assert (
        "lib2" in entries
        and "lib3" in entries
        and "__init__" in entries
        and "resource" not in entries
    )


def test_cyclic_alias():
    packages = static.get_apis_from_wheel(
        "pymongo",
        "tests/resource/pymongo-3.12.0-cp39-cp39-manylinux1_i686.whl",
    )
    for pkg in packages:
        for entity in pkg.entities.values():
            if isinstance(entity, Alias):
                print(entity)
                try:
                    pkg.get(pkg.full_name + "." + entity.name)
                except KeyError as ex:
                    print(pkg.full_name, entity.name, ex)
                    assert "cyclic" in str(ex) or not str(ex).startswith(pkg.name)


def test_cython():
    packages = static.get_apis_from_wheel(
        "Cython",
        "tests/resource/Cython-0.29.24-py2.py3-none-any.whl",
    )
    print([p.name for p in packages])
    assert set(p.name for p in packages) == set(["Cython", "cython", "pyximport"])
    for pkg in packages:
        if pkg.name == "cython":
            print(pkg)
            assert "cython.os" in pkg and "cython.sys" in pkg
            assert pkg["cython.main"].full_alias == "Cython.Compiler.Main.main"
            assert pkg["cython.*"].full_aliases == ["Cython.Shadow.*"]
            assert pkg["cython.__version__"].full_alias == "Cython.__version__"
            assert (
                pkg["cython.load_ipython_extension"].full_alias
                == "Cython.load_ipython_extension"
            )
            top_levels = {p.name: p for p in packages}
            assert pkg.get("cython.CythonTypeObject", top_levels=top_levels)
            assert pkg.get("cython.compiled", top_levels=top_levels)


def test_numpy():
    """Numpy have a lot of wildcard imports and .pyi files"""
    packages = static.get_apis_from_wheel(
        "numpy",
        "tests/resource/numpy-1.21.2-pp37-pypy37_pp73-manylinux_2_12_x86_64.manylinux2010_x86_64.whl",
    )
    packages = {p.name: p for p in packages}
    assert isinstance(packages["numpy"].get("numpy.Inf"), Variable)
    assert isinstance(packages["numpy"].get("numpy.around"), Function)
    assert isinstance(packages["numpy"].get("numpy._mat"), Package)
    assert packages["numpy"]["numpy.arcsinh"]


def test_matplotlib():
    matplotlib = static.get_apis_from_wheel(
        "matplotlib",
        "tests/resource/matplotlib-3.4.3-pp37-pypy37_pp73-manylinux2010_x86_64.whl",
    )
    numpy = static.get_apis_from_wheel(
        "numpy",
        "tests/resource/numpy-1.21.2-pp37-pypy37_pp73-manylinux_2_12_x86_64.manylinux2010_x86_64.whl",
    )
    matplotlib = {p.name: p for p in matplotlib}
    numpy = {p.name: p for p in numpy}
    matplotlib.update(numpy)

    assert matplotlib["pylab"].get("pylab.argmax", top_levels=matplotlib)


def test_pyi():
    pkg = static.get_apis_from_wheel(
        "markupsafe",
        "tests/resource/MarkupSafe-2.0.1-cp39-cp39-manylinux1_i686.whl",
    )
    pkg = {p.name: p for p in pkg}

    print([e.name for e in pkg["markupsafe"].entities.values()])
    print(pkg["markupsafe"]["markupsafe.escape"])
    print(pkg["markupsafe"]["markupsafe.soft_str"])
    print(pkg["markupsafe"]["markupsafe._speedups"])

    assert pkg["markupsafe"].get("markupsafe.escape")
    assert pkg["markupsafe"].get("markupsafe.soft_str")
