import py4a.api.extractor as e
from py4a.api.extractor import *


def test_is_valid_version():
    assert e._is_valid_version("0.0.1")
    assert e._is_valid_version("1.55")
    assert not e._is_valid_version("0.0.1-dev")
    assert not e._is_valid_version("0.0.1.dev")
    assert not e._is_valid_version("1.0.0-alpha+001")


def test_page_num():
    assert e._page_num(30, 90) == 3
    assert e._page_num(30, 91) == 4


def test_select_wheel():
    whl = e._select_wheel(
        [
            {"filename": "pandas-1.3.0.tar.gz"},
            {"filename": "pandas-1.3.0-cp39-cp39-win32.whl"},
            {"filename": "pandas-1.3.0-cp39-cp39-manylinux.whl"},
            {"filename": "pandas-1.3.0-cp39-cp39-macosx_10_9_x86_64.whl"},
            {"filename": "pandas-1.3.0-cp37-cp37m-manylinux_2_5_i686.whl"},
        ]
    )
    assert whl["filename"] == "pandas-1.3.0-cp39-cp39-manylinux.whl"
