import json
import logging
import os
import re

import requests

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok"),
}

FAIL_RESPONSE = {
    "statusCode": 500,
    "headers": {"Content-Type": "application/json"},
    "body": "",
}


def _validate_title(title):
    return title.startswith("NO-TICKET") or bool(re.match(r"\w+\-\d+", title))


def _validate_commits(pull_request):
    commits = _get_commits(pull_request["commits_url"])

    for commit_parent in commits:
        message = commit_parent["commit"]["message"]
        if not message.lower().startswith("merge") and not _validate_title(message):
            return False

    return True


def _get_commits(url):
    pass


def _validate_pr(pull_request):
    if _validate_title(pull_request["title"]):

        return True, "Your PR title is ok!"
    else:
        return False, "Your PR title should start with NO-TICKET or a ticket id"


def _get_gh_headers():
    token = os.environ["GITHUB_TOKEN"]
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _update_pr_status(url, state, check_title, check_description):
    headers = _get_gh_headers()
    body = {"context": check_title, "description": check_description, "state": state}

    return requests.post(url, json=body, headers=headers)


def _get_failure_response(gh_response):
    logger.error("Error from gh:" + str(gh_response))
    return {**FAIL_RESPONSE, "body": gh_response.text}


def handler(event, context):
    ghevent = json.loads(event.get("body"))
    status_url = ghevent["pull_request"]["statuses_url"]

    valid_pr, reason = _validate_pr(ghevent["pull_request"])
    status = "success" if valid_pr else "failure"

    gh_response = _update_pr_status(status_url, status, "PR standard", reason)

    if gh_response.ok:
        return OK_RESPONSE

    return _get_failure_response(gh_response)
