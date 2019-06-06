from .flake8 import Flake8Adapter
from .eslint import EslintAdapter

adapter_map = {"flake8": Flake8Adapter, "eslint": EslintAdapter}


def create_quality_adapter(content):
    for key in adapter_map.keys():
        if f"Quality Report: {key}" in content:
            adapter = adapter_map[key]
            return adapter(content)

    raise Exception("Unknown adapter")
