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
CHECK_TITLE = "FineTune Standard"
ALLOWED_COMMITS = ["[shepherd]", "Merge"]

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok"),
}


def _validate_title(title):
    return title.startswith("NO-TICKET") or bool(re.match(r"\w+\-\d+", title))


def _validate_commits(pull_request):
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
    title_valid = _validate_title(pull_request["title"])
    commits, all_commits_ok = _validate_commits(pull_request)

    report = {
        "title": {"message": pull_request["title"], "standard": title_valid},
        "commits": commits,
    }

    if not title_valid:
        result = False
        reason = PR_TITLE_FAILURE_MESSAGE
    elif not all_commits_ok:
        result = False
        reason = PR_COMMITS_FAILURE_MESSAGE
    else:
        result = True
        reason = SUCCESS_MESSAGE

    result = title_valid and all_commits_ok
    return report, result, reason


@error_handler.wrapper_for("github")
def handler(event, context):
    ghevent = json.loads(event.get("body"))
    status_url = ghevent["pull_request"]["statuses_url"]

    report, result, reason = _validate_pr(ghevent["pull_request"])

    status = "success" if result else "failure"
    logger.info(f"Updating PR status to {status} due {reason}")

    github.update_pr_status(status_url, status, CHECK_TITLE, reason)

    # if not valid_pr and len(commits_analyzed) > 0:
    #     logger.info("Invalid commits found - Writing summary")
    #     github.write_standard_summary(
    #         ghevent["pull_request"]["comments_url"], commits_analyzed
    #     )
    #     logger.info("Summary written")

    return OK_RESPONSE
