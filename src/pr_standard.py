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


def _validate_commits(commits):
    for commit_parent in commits:
        if not _validate_title(commit_parent["commit"]["message"]):
            return False

    return True


def _validate_pr(pull_request):
    return _validate_title(pull_request["title"])


def _update_pr_status(url, state, check_title, check_description):
    token = os.environ["GITHUB_TOKEN"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    body = {"context": check_title, "description": check_description, "state": state}

    return requests.post(url, json=body, headers=headers)


def _get_failure_response(gh_response):
    logger.error("Error from gh:" + str(gh_response))
    return {**FAIL_RESPONSE, "body": gh_response.text}


def handler(event, context):
    ghevent = json.loads(event.get("body"))
    pr_url = ghevent["pull_request"]["statuses_url"]

    if _validate_pr(ghevent["pull_request"]):
        gh_response = _update_pr_status(
            pr_url, "success", "PR standard", "Your PR title is ok!"
        )
    else:
        gh_response = _update_pr_status(
            pr_url,
            "failure",
            "PR standard",
            "Your PR title should start with NO-TICKET or a ticket id",
        )

    if gh_response.ok:
        return OK_RESPONSE

    return _get_failure_response(gh_response)
