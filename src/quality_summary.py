import json
import re

try:
    import s3
    import circleci
except ModuleNotFoundError:  # For tests
    from . import s3
    from . import circleci

COV_EMPTY_TEXT = "No lines with coverage information in this diff."
COV_REPORT_FOOTER = "See details in the [**coverage report**](#COV_LINK#)."
QUALITY_EMPTY_TEXT = "No lines with quality information in this diff."
QUALITY_REPORT_FOOTER = "See details in the [**quality report**](#QUALITY_LINK#)."


def _get_reports_link(owner, project, build_num):
    artifacts = circleci.get_artifacts_from_build(owner, project, build_num)
    reports = {
        "coverage": {"name": "coverage.html", "url": ""},
        "flake8": {"name": "flake8.html", "url": ""},
    }

    for artifact in artifacts:
        for key in reports.keys():
            if artifact["path"].endswith(reports[key]["name"]):
                reports[key]["url"] = artifact["url"]

    return reports


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


def _read_quality_file(hash):
    content = s3.get_quality_file(hash)

    if content and QUALITY_EMPTY_TEXT not in content:
        report = {}
        report["target_branch"] = re.search(r"Diff: (.*)\.\.\.", content).group(1)
        report["total"] = re.search(r"Total: (.*) lines", content).group(1).strip()
        report["violations"] = (
            re.search(r"Violations: (.*) lines", content).group(1).strip()
        )
        report["quality"] = re.search(r"Quality: (.*)", content).group(1).strip()

        matches = re.findall(r"(.*):(\d+): ([A-Z]\d+) (.*)", content)
        report["issues"] = matches

        matches = re.findall(r"(.*) \((.*)\)", content)
        report["files"] = matches

        return report

    return False


def handler(event, context):
    cievent = json.loads(event.get("body"))

    commit_sha = cievent["commit_sha"]

    _read_coverage_file(commit_sha)
