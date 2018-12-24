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


def _get_edit_url(url, *args):
    """
    Try to retrieve a comment_id by looking for any args inside text
    """
    headers = _get_gh_headers()
    USER = os.environ.get("GITHUB_USER")

    response = requests.get(url, headers=headers)
    comments = response.json()

    for comment in comments:
        if any(text in comment["body"] for text in args):
            if comment["user"]["login"] == USER:
                return comment["url"]

    # Not comment to edit, it should be created
    return False


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


def write_quality_summary(url, cov_report, quality_report, cov_footer, quality_footer):
    headers = _get_gh_headers()

    cov_summary = summary_factory.create_coverage_summary(cov_report, cov_footer)
    quality_summary = summary_factory.create_quality_summary(
        quality_report, quality_footer
    )

    # TODO: What if both reports are empty?
    body = {"body": f"{cov_summary}\n{quality_summary}"}

    edit_url = _get_edit_url(url, "Coverage Diff", "Quality Diff")
    if edit_url:
        return requests.patch(edit_url, json=body, headers=headers)
    else:
        return requests.post(url, json=body, headers=headers)
