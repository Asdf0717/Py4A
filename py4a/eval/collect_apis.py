"""Small script to dynamically collect APIs from a module"""

import sys
import json
from inspect import isfunction, isclass, ismodule


if __name__ == "__main__":
    top_level = sys.argv[1]
    try:
        exec("import " + top_level)
        exec("names = dir(" + top_level + ")")
        result = []
        for name in names:
            if name.startswith("__") and name.endswith("__"):
                continue
            type = "Variable"
            exec("api = " + top_level + "." + name)
            if isclass(api):
                type = "Class"
            elif isfunction(api) or callable(api):
                type = "Function"
            elif ismodule(api):
                type = "Package"
            result.append((top_level + "." + name, type))
        print(json.dumps(result))
    except Exception as ex:
        print(f"[]")
        sys.exit(1)
