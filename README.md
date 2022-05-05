# Py4A

## Initialize Development

```shell
conda create -n py4a python=3.9
conda activate py4a
pip install -r requirements.txt
pip install -U pytest black pytest-cov
conda install -c conda-forge jupyterlab
```

## Lint and Run all tests

Use command `black py4a tests` to reformat all code. Use command `pytest` to run all tests. Use `pytest -r P` to run with detailed output for each test.

## Usage

### Extract APIs for One Package

Commands like this will take some time to finish. Details about API extraction will be stored in JSON files: `{pkg_name}-static-api-summary.json` and `{pkg_name}-dynamic-api-summary.json`.

```shell
nohup python -m py4a.api.extractor -v requests psf/requests > logs/requests.log &
nohup python -m py4a.api.extractor -v pandas pandas-dev/pandas > logs/pandas.log & 
```

### Retrieve Package Data to Build an API Knowledge Base

```shell
nohup python -m py4a.api.stdlib > logs/stdlib.log &
nohup python -m py4a.get_package_data --limit 10000 > logs/get_package_data.log &
nohup python -m py4a.get_package_data --limit 10000 --dynamic > logs/get_package_data.log &
```

### Retrieve Client API Usages

```shell
nohup python -m py4a.get_api_usage -p pandas,tensorflow,scikit-learn,keras,django,flask \
    --output-dir=output/ --overwrite > logs/get_api_usage_static.log &
nohup python -m py4a.get_api_usage -p pandas,tensorflow,scikit-learn,keras,django,flask \
    --output-dir=output/ --all > logs/get_api_usage_static_all.log &
```

### Analyze Package API Evolution and Breaking Changes

```shell
nohup python -m py4a.get_api_changes -p pandas,tensorflow,scikit-learn,keras,django,flask \
    --output-dir=output/static --client > logs/get_api_changes_static.log &
```
