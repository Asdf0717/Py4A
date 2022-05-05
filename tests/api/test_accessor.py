from py4a.api.accessor import *
from py4a.api.extractor import *


def test_accessor():
    pkg_name = "pandas"
    if not has_metadata(pkg_name) or not has_api(pkg_name) or not has_req(pkg_name):
        download_package(pkg_name, METADATA_PATH, PKG_PATH)
        extract_api_static(pkg_name, PKG_PATH, STATIC_API_PATH)
        extract_requirements(pkg_name, PKG_PATH, REQ_PATH)
    assert has_metadata(pkg_name) and has_api(pkg_name)
    assert "1.0.0" in get_vers_with_apis(pkg_name)
    assert "pandas" in get_apis(pkg_name, "1.0.0").keys()
    assert "pandas" in get_wheel_path(pkg_name, "1.0.0")
    assert any(
        d.name == "numpy" for d in get_requirements(pkg_name, "1.0.0").require_deps
    )
