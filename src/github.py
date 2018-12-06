import os

import requests


def _get_gh_headers():
    token = os.environ["GITHUB_TOKEN"]
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_commits(url):
    headers = _get_gh_headers()
    response = requests.get(url, headers=headers)
    return response.json()


def update_pr_status(url, state, check_title, check_description):
    headers = _get_gh_headers()
    body = {"context": check_title, "description": check_description, "state": state}

    return requests.post(url, json=body, headers=headers)
