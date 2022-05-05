## jsonschema 4.2.0

### Steps to Reproduce

```
conda create -n test python=3.8
conda activate test
pip install jsonschema==4.2.0 importlib-resources==1.0.2
python -c "import jsonschema._utils"
```

### Output

```
$ python -c "import jsonschema._utils"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/heh/anaconda3/envs/test/lib/python3.8/site-packages/jsonschema/__init__.py", line 29, in <module>
    from jsonschema.validators import (
  File "/home/heh/anaconda3/envs/test/lib/python3.8/site-packages/jsonschema/validators.py", line 349, in <module>
    meta_schema=_utils.load_schema("draft3"),
  File "/home/heh/anaconda3/envs/test/lib/python3.8/site-packages/jsonschema/_utils.py", line 60, in load_schema
    path = resources.files(__package__).joinpath(f"schemas/{name}.json")
AttributeError: module 'importlib_resources' has no attribute 'files'
```

### Status

Reported in https://github.com/Julian/jsonschema/issues/876
Already Fixed in https://github.com/Julian/jsonschema/pull/877

## requests-toolbelt 0.1.1

### Steps to Reproduce

```
conda create -n test python=3.9
conda activate test
pip install request==2.16.0 request-toolbelt=0.1.1
python -c "import requests_toolbelt.multipart"
```

### Output

```
$ python -c "import requests_toolbelt.multipart"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/heh/anaconda3/envs/test/lib/python3.9/site-packages/requests_toolbelt/__init__.py", line 19, in <module>
    from .multipart import MultipartEncoder
  File "/home/heh/anaconda3/envs/test/lib/python3.9/site-packages/requests_toolbelt/multipart.py", line 12, in <module>
    from requests.packages.urllib3.filepost import (iter_field_objects,
ModuleNotFoundError: No module named 'requests.packages'
```

### Status

Fixed in https://github.com/psf/requests/commit/267ec2f9c32d16c17eb979cab1eb9b9feb8b5217

