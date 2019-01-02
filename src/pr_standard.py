import json
import logging
import re

try:
    from thirdparties import github
    import error_handler
except ModuleNotFoundError:  # For tests
    from .thirdparties import github
    from . import error_handler

logger = logging.getLogger()

CHECK_TITLE = "FineTune Standard"
ALLOWED_COMMITS = ["[shepherd]", "Merge"]
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
    return title.startswith("NO-TICKET") or bool(re.match(r"\w+\-\d+", title))


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

        if not _validate_title(commit["message"]):
            standard = any(
                commit["message"].startswith(allowed) for allowed in ALLOWED_COMMITS
            )
        else:
            standard = True

        commit["standard"] = standard
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

    result = title_valid and all_commits_ok
    return report, result, reason


@error_handler.wrapper_for("github")
def handler(event, context):
    """
    Lambda handler expecting a Pull Request event from GitHub.
    It sends a status update to the PR, and writes a summary
    with detailed information.
    """
    ghevent = json.loads(event.get("body"))
    status_url = ghevent["pull_request"]["statuses_url"]

    report, result, reason = _validate_pr(ghevent["pull_request"])
    status = "success" if result else "failure"

    print(f"Updating PR status to {status} due {reason}")
    github.update_pr_status(status_url, status, CHECK_TITLE, reason)

    print(f"Writing PR summary for report: {report}")
    github.write_standard_summary(ghevent["pull_request"]["comments_url"], report)

    return OK_RESPONSE
