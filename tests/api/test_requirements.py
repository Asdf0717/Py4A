import jsonpickle

from py4a.api.accessor import *
from py4a.api.requirements import *


def test_get_requirements():
    req = Requirements(
        "pandas",
        "1.3.2",
        "tests/resource/pandas-1.3.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    )
    print(jsonpickle.encode(req, indent=2))
    assert any(dep.name == "numpy" for dep in req.require_deps)
