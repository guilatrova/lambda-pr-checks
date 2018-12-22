import json
import re

try:
    import s3
    import circleci
    import github
except ModuleNotFoundError:  # For tests
    from . import s3
    from . import circleci
    from . import github

COV_EMPTY_TEXT = "No lines with coverage information in this diff."
COV_REPORT_FOOTER = "See details in the [**coverage report**](#COV_LINK#)."
QUALITY_EMPTY_TEXT = "No lines with quality information in this diff."
QUALITY_REPORT_FOOTER = "See details in the [**quality report**](#QUALITY_LINK#)."


def _get_footers(cievent):
    report_links = _get_reports_link(
        cievent["owner"], cievent["project"], cievent["build_num"]
    )

    return {
        "quality": QUALITY_REPORT_FOOTER.replace(
            "#QUALITY_LINK#", report_links.get("flake8", "")
        ),
        "coverage": COV_REPORT_FOOTER.replace(
            "#COV_LINK#", report_links.get("coverage", "")
        ),
    }


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


def _extract_pr_data(raw_url):
    """
    Extracts owner, repo and PR number from regular PR url.
    Expected format: https://github.com/:owner/:repo/pull/:number
    """
    matches = re.findall(r"github\.com\/(.*)\/(.*)\/pull\/(\d+)", raw_url)[0]
    return {"owner": matches[0], "repo": matches[1], "pr_number": matches[2]}


def _get_pr_urls(raw_url, commit_sha):
    """
    Returns a tuple with Summary URL and Status URL
    """
    data = _extract_pr_data(raw_url)
    owner = data["owner"]
    repo = data["repo"]
    pr_number = data["pr_number"]

    summary_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    )
    statuses_url = f"https://api.github.com/repos/{owner}/{repo}/statuses/{commit_sha}"

    return (summary_url, statuses_url)


def _update_github_status_summary(
    summary_url, statuses_url, cov_report, quality_report, footers
):
    # Summary
    github.write_quality_summary(
        summary_url, cov_report, quality_report, footers["coverage"], footers["quality"]
    )

    # Status
    # pr_state = "success" if condition else "failure"
    # description = "Coverage x% and Quality y%"
    # github.update_pr_status(status_url, pr_state, "FineTune Coverage", description)
    # github.update_pr_status(status_url, pr_state, "FineTune Quality", description)


def ci_handler(event, context):
    cievent = json.loads(event.get("body"))
    commit_sha = cievent["commit_sha"]

    cov_report = _read_coverage_file(commit_sha)
    quality_report = _read_quality_file(commit_sha)

    if cievent["pr_link"]:
        # Expected format: https://github.com/:owner/:repo/pull/:number
        summary_url, statuses_url = _get_pr_urls(cievent["pr_link"])
        footers = _get_footers(cievent)

        _update_github_status_summary(
            summary_url, statuses_url, cov_report, quality_report, footers
        )
