import json
import re

try:
    import s3
except ModuleNotFoundError:  # For tests
    from . import s3

COV_EMPTY_TEXT = "No lines with coverage information in this diff."


def _read_coverage_file(hash):
    content = s3.get_coverage_file(hash)

    if content and COV_EMPTY_TEXT not in content:
        report = {}
        report["target_branch"] = re.search(r"Diff: (.*)\.\.\.", content).group(1)
        report["total"] = re.search(r"Total: (.*) lines", content).group(1).strip()
        report["missing"] = re.search(r"Missing: (.*) lines", content).group(1).strip()
        report["coverage"] = re.search(r"Coverage: (.*)", content).group(1).strip()

        matches = re.findall(r"(.*) \((.*)\)(.*)", content)
        report["files"] = matches

        return report

    return False


def handler(event, context):
    cievent = json.loads(event.get("body"))

    commit_sha = cievent["commit_sha"]

    _read_coverage_file(commit_sha)
