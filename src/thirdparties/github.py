import logging
import os

import requests

try:
    from thirdparties import summary_factory
except ModuleNotFoundError:  # For tests
    from . import summary_factory


logger = logging.getLogger()


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


def _get_comment_url(url, *args):
    """
    Try to retrieve comment_url by looking for any args inside text body.

    It also makes sure the owner of that comment has the same username set
    in env var GITHUB_USER, to avoid mistakes.
    """
    headers = _get_gh_headers()
    USER = os.environ.get("GITHUB_USER")

    response = requests.get(url, headers=headers)
    comments = response.json()

    for comment in comments:
        if any(text in comment["body"] for text in args):
            if comment["user"]["login"] == USER:
                return comment["url"]

    # No comment to edit, it should be created
    return False


def get_commits(url):
    headers = _get_gh_headers()
    response = requests.get(url, headers=headers)
    return response.json()


def update_pr_status(url, state, check_title, check_description="", details_url=""):
    headers = _get_gh_headers()
    body = {"context": check_title, "description": check_description, "state": state, "target_url": details_url}

    return requests.post(url, json=body, headers=headers)


def get_open_prs(repo):
    url = f"https://api.github.com/repos/{repo}/pulls?state=open"
    headers = _get_gh_headers()

    response = requests.get(url, headers=headers)
    return response.json()


def get_repo_id(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = _get_gh_headers()

    response = requests.get(url, headers=headers)
    content = response.json()
    return content["id"]


def delete_standard_summary(url):
    delete_url = _get_comment_url(url, "Guidelines Report")
    if delete_url:
        headers = _get_gh_headers()
        return requests.delete(delete_url, headers=headers)


def write_standard_summary(url, report, resume):
    headers = _get_gh_headers()
    body = {"body": summary_factory.create_standard_summary(report, resume)}

    edit_url = _get_comment_url(url, "Guidelines Report")
    if edit_url:
        return requests.patch(edit_url, json=body, headers=headers)

    return requests.post(url, json=body, headers=headers)


def write_quality_summary(url, cov_report, quality_report, cov_footer, quality_footer):
    headers = _get_gh_headers()

    comment_keys_to_find = ["Quality Report", "Coverage Report"]
    if cov_report or quality_report:
        cov_summary = summary_factory.create_coverage_summary(cov_report, cov_footer)
        quality_summary = summary_factory.create_quality_summary(
            quality_report, quality_footer
        )

        body = {"body": f"{cov_summary}\n{quality_summary}"}

        edit_url = _get_comment_url(url, *comment_keys_to_find)
        if edit_url:
            return requests.patch(edit_url, json=body, headers=headers)
        else:
            return requests.post(url, json=body, headers=headers)
    else:
        print(
            "No report provided, so no summary to write."
            + "Let's check if we need to delete something."
        )
        delete_url = _get_comment_url(url, *comment_keys_to_find)

        if delete_url:
            return requests.delete(delete_url, headers=headers)
