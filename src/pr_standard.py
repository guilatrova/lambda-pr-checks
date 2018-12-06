import json
import os
import re

import requests

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok"),
}


def _validate_pr_title(title):
    return title.startswith("NO-TICKET") or bool(re.match(r"\w+\-\d+", title))


def _update_pr_status(url, state, check_title, check_description):
    token = os.environ["GITHUB_TOKEN"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    body = {"context": check_title, "description": check_description, "state": state}

    requests.post(url, json=body, headers=headers)


def handler(event, context):
    ghevent = json.loads(event.get("body"))

    pr_url = ghevent.pull_request.url
    if _validate_pr_title(ghevent.pull_request.title):
        _update_pr_status(pr_url, "success", "PR standard", "Your PR title is ok!")
    else:
        _update_pr_status(
            pr_url,
            "failure",
            "PR standard",
            "Your PR title should start with NO-TICKET or a ticket id",
        )

    return OK_RESPONSE
