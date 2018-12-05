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
    return title.startswith("NO-TICKET") or re.match(r"\w+\-\d+")


def _update_pr_status(url, state, check_title, check_description):
    token = os.environ["GITHUB_TOKEN"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    body = {"context": check_title, "description": check_description, "state": state}

    requests.post(url, json=body, headers=headers)


def pr_standard(event, context):
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


# def hello(event, context):
#     body = {
#         "message": "Go Serverless v1.0! Your function executed successfully!",
#         "input": event
#     }

#     response = {
#         "statusCode": 200,
#         "body": json.dumps(body)
#     }

#     return response

#     # Use this code if you don't use the http event with the LAMBDA-PROXY
#     # integration
#     """
#     return {
#         "message": "Go Serverless v1.0! Your function executed successfully!",
#         "event": event
#     }
#     """
