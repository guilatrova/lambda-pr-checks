import os
import json
import logging
import re

try:
    from thirdparties import github
    import error_handler
    import security
except ModuleNotFoundError:  # For tests
    from .thirdparties import github
    from . import error_handler
    from . import security

logger = logging.getLogger()

CHECK_TITLE = "FineTune Standard"
ALLOWED_COMMITS = [
    r"^\w+\-\d+",
    r"^NO-TICKET",
    r"^\[shepherd\]",
    r"^Merge",
    r"Release \d{8}",
]

# reasons
SUCCESS_REASON = "Your PR is up to standards!"
TITLE_FAILURE_REASON = "Your PR title is not up to standards"
COMMITS_FAILURE_REASON = "Your PR has some commits not up to standards"

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok"),
}


def _validate_title(title):
    return any(re.match(allowed, title) for allowed in ALLOWED_COMMITS)


def _validate_commits(pull_request):
    """
    Retrieves all commits in PR and loop them validating every single message.

    Returns a tuple (commits, result) in following format
        1: commits:
            [
                {
                    sha: string
                    message: string
                    standard: bool
                },
            ]
        2: result: Whether ALL commits are up to standard
    """
    commits = github.get_commits(pull_request["commits_url"])
    analyzed = []

    for commit_wrapper in commits:
        commit = {
            "sha": commit_wrapper["sha"],
            "message": commit_wrapper["commit"]["message"],
        }

        commit["standard"] = _validate_title(commit["message"])
        analyzed.append(commit)

    result = all(commit["standard"] for commit in analyzed)
    return analyzed, result


def _validate_pr(pull_request):
    """
    Returns a tuple with report, result, reason
        report: A dict in the following format
            title:
                message: string
                standard: bool
            commits:
                [
                    {
                        sha: string
                        message: string
                        standard: bool
                    },
                ]
        result: Whether it's valid
        reason: Why did it succeed or failed
    """
    title_valid = _validate_title(pull_request["title"])
    commits, all_commits_ok = _validate_commits(pull_request)

    report = {
        "title": {"message": pull_request["title"], "standard": title_valid},
        "commits": commits,
    }

    if not title_valid:
        result = False
        reason = TITLE_FAILURE_REASON
    elif not all_commits_ok:
        result = False
        reason = COMMITS_FAILURE_REASON
    else:
        result = True
        reason = SUCCESS_REASON

    return report, result, reason


@error_handler.wrapper_for("github")
@security.secret_handler("X-Hub-Signature")
def handler(event, context):
    """
    Lambda handler expecting a Pull Request event from GitHub.
    It sends a status update to the PR, and writes a summary
    with detailed information.
    """
    ghevent = json.loads(event.get("body"))
    status_url = ghevent["pull_request"]["statuses_url"]
    comments_url = ghevent["pull_request"]["comments_url"]

    report, result, reason = _validate_pr(ghevent["pull_request"])
    status = "success" if result else "failure"

    print(f"Updating PR status to {status} due {reason}")
    target_url = os.environ.get("DOCS_STANDARD_LINK", "")
    github.update_pr_status(status_url, status, CHECK_TITLE, reason, target_url)

    if result:
        print(f"Everything is perfect: {report}, no standard summary will be written")
        github.delete_standard_summary(comments_url)
    else:
        print(f"Writing PR summary for report: {report}")
        github.write_standard_summary(
            comments_url, report, reason
        )

    return OK_RESPONSE
