import json
import re

try:
    import s3
except ModuleNotFoundError:  # For tests
    from . import s3


def _read_coverage_file(hash):
    content = s3.get_coverage_file(hash)
    if content:
        matches = re.findall(r"(.*) \((.*)\)(.*)", content)
        return matches

    return []


def handler(event, context):
    cievent = json.loads(event.get("body"))

    commit_sha = cievent["commit_sha"]

    _read_coverage_file(commit_sha)
