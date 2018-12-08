import os

import requests

ERROR_SUMMARY = """
Some patterns errors were found:

```diff
Commits
=============
#PLACEHOLDER#
```

Read the [docs](#DOCS#) for more details
"""


def _get_gh_headers():
    token = os.environ["GITHUB_TOKEN"]
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _create_summary_content(commits):
    content = []
    for commit in commits:
        standard = "+" if commit["standard"] else "-"
        sha = commit["sha"][:7]
        message = commit["message"]
        content.append(f"{standard} {sha} {message}")

    joined = "\n".join(content)

    summary = ERROR_SUMMARY.replace("#PLACEHOLDER#", joined)
    summary = summary.replace("#DOCS#", os.environ.get("DOCS_STANDARD_LINK", ""))

    return summary.strip()


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


def write_error_summary(url, analyzed):
    headers = _get_gh_headers()
    body = {"body": _create_summary_content(analyzed)}

    return requests.post(url, json=body, headers=headers)
