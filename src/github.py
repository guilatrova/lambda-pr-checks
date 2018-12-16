import os

import requests

try:
    import summary_factory
except ModuleNotFoundError:  # For tests
    from . import summary_factory


class GitHubException(Exception):
    def __init__(self, url, response_text):
        super().__init__()
        self.url = url
        self.response_text = response_text


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


def update_pr_status(url, state, check_title, check_description=""):
    headers = _get_gh_headers()
    body = {"context": check_title, "description": check_description, "state": state}

    return requests.post(url, json=body, headers=headers)


def get_open_prs(repo):
    url = f"https://api.github.com/repos/{repo}/pulls?state=open"
    headers = _get_gh_headers()

    response = requests.get(url, headers=headers)
    return response.json()


def write_standard_summary(url, analyzed):
    headers = _get_gh_headers()
    body = {"body": summary_factory.create_standard_summary(analyzed)}

    return requests.post(url, json=body, headers=headers)


def write_quality_summary(url, cov_report, quality_report):
    pass
