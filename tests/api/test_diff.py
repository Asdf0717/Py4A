import py4a.api.accessor as accessor
import py4a.api.dynamic as dynamic
from py4a.api.diff import diff_pkg


def test_diff():
    all_vers = accessor.get_vers_with_apis("pandas", dynamic=False)
    vers = ["1.0.0", "1.3.2", "1.3.3"]
    apis = [None, None, None]
    for i, ver in enumerate(vers):
        if ver in all_vers:
            apis[i] = accessor.get_apis("pandas", ver, dynamic=False)
        else:
            apis[i], failed = dynamic.get_apis_from_runtime("pandas", ver, ["pandas"])
    for d in diff_pkg(apis[1], apis[2]):
        print(d)
    for d in diff_pkg(apis[0], apis[2]):
        print(d)
