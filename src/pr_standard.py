import json
import logging
import re

try:
    import github
    import error_handler
except ModuleNotFoundError:  # For tests
    from . import github
    from . import error_handler

logger = logging.getLogger()

SUCCESS_MESSAGE = "Your PR is ok!"
PR_TITLE_FAILURE_MESSAGE = "Your PR title should start with NO-TICKET or a ticket id"
PR_COMMITS_FAILURE_MESSAGE = "Your PR has some commits with invalid format"
ALLOWED =

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok"),
}


def _validate_title(title):
    return title.startswith("NO-TICKET") or bool(re.match(r"\w+\-\d+", title))


def _validate_commits(pull_request):
    commits = github.get_commits(pull_request["commits_url"])
    result = True
    analyzed = []

    for commit_wrapper in commits:
        commit_obj = commit_wrapper["commit"]
        commit = {
            "sha": commit_wrapper["sha"],
            "message": commit_obj["message"],
            "standard": True,
        }

        if not commit["message"].lower().startswith("merge") and not _validate_title(
            commit["message"]
        ):
            result = False
            commit["standard"] = False

        analyzed.append(commit)

    return result, analyzed


def _validate_pr(pull_request):
    if _validate_title(pull_request["title"]):
        valid_commits, commits_analyzed = _validate_commits(pull_request)

        if valid_commits:
            return True, SUCCESS_MESSAGE, commits_analyzed
        else:
            return False, PR_COMMITS_FAILURE_MESSAGE, commits_analyzed
    else:
        return False, PR_TITLE_FAILURE_MESSAGE, []


@error_handler.wrapper_for("github")
def handler(event, context):
    logger.info("Handler start")
    ghevent = json.loads(event.get("body"))
    status_url = ghevent["pull_request"]["statuses_url"]

    valid_pr, reason, commits_analyzed = _validate_pr(ghevent["pull_request"])
    status = "success" if valid_pr else "failure"
    logger.info("Updating PR status: " + status)

    github.update_pr_status(status_url, status, "PR standard", reason)
    logger.info("PR status updated")

    if not valid_pr and len(commits_analyzed) > 0:
        logger.info("Invalid commits found - Writing summary")
        github.write_standard_summary(
            ghevent["pull_request"]["comments_url"], commits_analyzed
        )
        logger.info("Summary written")

    return OK_RESPONSE
