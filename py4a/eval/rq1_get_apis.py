import os
import py4a.api.entity as entity
import py4a.api.accessor as accessor

if __name__ == "__main__":
    for f in os.listdir("evaluation/apis-snifferdog"):
        lib = "-".join(f.split("-")[:-1])
        ver = f.split("-")[-1].replace(".txt", "")
        print(f"{lib} {ver}")
        apis = accessor.get_apis(lib, ver)
        runtime = accessor.get_runtime(lib, ver, "3.9.6")
        api_names = set()
        for top_level in apis.keys():
            for key in apis[top_level].keys():
                api_names.add(key)
                try:
                    e = apis[top_level].get(key, runtime)
                    if isinstance(e, entity.Class):
                        api_names.update([key + "." + n for n in e.get_names()])
                except KeyError:
                    continue
        with open(f"evaluation/apis/{lib}-{ver}.txt", "w") as f:
            for name in sorted(api_names):
                f.write(f"{name}\n")
        