import json
import re

try:
    from thirdparties import github
    from aws import dynamodb, s3
    from qualitytools.factory import create_quality_adapter
    from CircleCommitDTO import CircleCommitDTO
    import error_handler
    import security
except ModuleNotFoundError:  # For tests
    from .thirdparties import github
    from .aws import dynamodb, s3
    from .qualitytools.factory import create_quality_adapter
    from .CircleCommitDTO import CircleCommitDTO
    from . import error_handler
    from . import security

COV_EMPTY_TEXT = "No lines with coverage information in this diff."
COV_REPORT_FOOTER = "See details in the [**coverage report**](#COV_LINK#)."
COV_THRESHOLD = 80

QUALITY_EMPTY_TEXT = "No lines with quality information in this diff."
QUALITY_REPORT_FOOTER = "See details in the [**quality report**](#QUALITY_LINK#)."
QUALITY_THRESHOLD = 100

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok"),
}


def _get_footers(reference):
    """
    Returns two footers to be appended to summaries
    """
    report_links = reference.get_reports_link()

    return {
        "quality": QUALITY_REPORT_FOOTER.replace(
            "#QUALITY_LINK#", report_links["flake8"].get("url", "")
        ),
        "coverage": COV_REPORT_FOOTER.replace(
            "#COV_LINK#", report_links["coverage"].get("url", "")
        )
    }


def _read_coverage_file(hash):
    """
    Generates a coverage report with info extracted from S3 file
    The report contains:
        "target_branch", "total", "missing", "coverage" and "files"
    """
    content = s3.get_coverage_file(hash)

    if content and COV_EMPTY_TEXT not in content:
        report = {}
        report["target_branch"] = re.search(r"Diff: (.*)\.\.\.", content).group(1)
        report["total"] = re.search(r"Total: (.*) line", content).group(1).strip()
        report["missing"] = re.search(r"Missing: (.*) line", content).group(1).strip()
        report["coverage"] = re.search(r"Coverage: (.*)", content).group(1).strip()

        matches = re.findall(r"(.*) \((.*)\)(.*)", content)
        report["files"] = [
            {"file": match[0], "value": match[1], "missing": match[2] or False}
            for match in matches
        ]

        return report

    return False


def _read_quality_file(hash):
    """
    Generates a quality report with info extracted from S3 file
    The report contains:
        "target_branch", "total", "violations", "quality", "issues" and "files"
    Rerturns a tuple with the report and quality tool
    """
    content = s3.get_quality_file(hash)

    quality_adapter, tool = create_quality_adapter(content)
    report = quality_adapter.generate_report()
    return report, tool


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


def _update_github_status(report, url, key, threshold, details_link):
    """
    Updates PR check status comparing data from report[key] to threshold
    """
    title = key.capitalize()

    if report:
        value = int(re.sub(r"\D", "", report[key]))
        if value >= threshold:
            pr_state = "success"
            description = f"{title} diff is good!"
        else:
            pr_state = "failure"
            description = (
                f"{title} diff is below expected ({value}% out of {threshold}%)"
            )
    else:
        pr_state = "success"
        description = "No report provided for this commit"
        details_link = ""  # If not report, don't provide the link

    github.update_pr_status(url, pr_state, f"FineTune {title}", description, details_link)


def _update_github_pr(summary_url, statuses_url, cov_report, quality_report, footers, report_links):
    """
    Updates GitHub PR with a summary and two checks for coverage and quality
    """
    # Summary
    github.write_quality_summary(
        summary_url, cov_report, quality_report, footers["coverage"], footers["quality"]
    )

    # PR checks
    cov_link = report_links.get("coverage", {}).get("url", "")
    qual_link = report_links.get("flake8", {}).get("url", "")

    _update_github_status(cov_report, statuses_url, "coverage", COV_THRESHOLD, cov_link)
    _update_github_status(quality_report, statuses_url, "quality", QUALITY_THRESHOLD, qual_link)


# Although it's CI, GitHub fail response fits good though
@error_handler.wrapper_for("github")
@security.secret_handler("Ft-Signature")
def ci_handler(event, context):
    """
    Expects to receive a payload from CircleCI with following info:
    "commit_sha", "owner", "project", "build_num", "pr_link" (pr_link might be empty).
    """
    cievent = json.loads(event.get("body"))

    cov_report = _read_coverage_file(cievent["commit_sha"])
    quality_report, quality_tool = _read_quality_file(cievent["commit_sha"])
    dynamodb.save_reports(cov_report, quality_report, quality_tool, **cievent)

    reference = CircleCommitDTO.create_from_circleci(cievent, quality_tool)

    if reference.pr_link:
        # Expected format: https://github.com/:owner/:repo/pull/:number
        reference.repo_id = github.get_repo_id(reference.owner, reference.project)

        summary_url, statuses_url = _get_pr_urls(cievent["pr_link"], reference.commit_sha)
        report_links = reference.get_reports_link()
        footers = _get_footers(reference)

        _update_github_pr(
            summary_url, statuses_url, cov_report, quality_report, footers, report_links
        )
    else:
        print("CI event will be ignored because PR_LINK is empty")

    return OK_RESPONSE


@error_handler.wrapper_for("github")
@security.secret_handler("X-Hub-Signature")
def gh_handler(event, context):
    ghevent = json.loads(event.get("body"))

    summary_url = ghevent["pull_request"]["comments_url"]
    statuses_url = ghevent["pull_request"]["statuses_url"]
    commit_sha = ghevent["pull_request"]["head"]["sha"]
    repo_id = ghevent["repository"]["id"]
    report = dynamodb.get_report(commit_sha)

    if report:
        reference = CircleCommitDTO.create_from_dynamodb(report, repo_id)
        report_links = reference.get_reports_link()
        footers = _get_footers(reference)

        cov_report = report.get("cov_report", False)
        quality_report = report.get("quality_report", False)

        _update_github_pr(
            summary_url, statuses_url, cov_report, quality_report, footers, report_links
        )
    else:
        print(f"No report found for {commit_sha}")

    return OK_RESPONSE
