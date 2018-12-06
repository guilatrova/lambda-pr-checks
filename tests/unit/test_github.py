import os
from unittest.mock import MagicMock

from src import github


def test_update_pr_status(mocker):
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "123456"})
    request = mocker.patch.object(github.requests, "post", return_value=None)

    headers = github._get_gh_headers()
    github.update_pr_status("url", "state", "context", "description")

    request.assert_called_once_with(
        "url",
        json={"context": "context", "state": "state", "description": "description"},
        headers=headers,
    )


def test_get_commits(mocker):
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "123456"})
    request = mocker.patch.object(github.requests, "get", return_value=MagicMock())

    headers = github._get_gh_headers()
    github.get_commits("url")

    request.assert_called_once_with("url", headers=headers)
