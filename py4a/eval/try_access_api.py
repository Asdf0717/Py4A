"""Simple script to access one given API entity"""

import sys
from inspect import isfunction, isclass

if __name__ == "__main__":
    api_name = sys.argv[1]
    api_type = sys.argv[2]

    module_name = ".".join(api_name.split(".")[:-1])

    try:
        exec("import " + module_name)
        exec("api = " + api_name)
    except Exception as ex:
        print(f"FAIL: {ex}")
        sys.exit(1)
    if api_type == "class" and isclass(api):
        print("OK")
    elif api_type == "function" and (isfunction(api) or callable(api)):
        print("OK")
    elif api_type == "other":
        print("OK")
    else:
        print(f"FAIL: Wrong type")
