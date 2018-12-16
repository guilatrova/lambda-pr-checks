import os
from unittest.mock import MagicMock

import pytest

from src import github


@pytest.fixture()
def expected_headers(mocker):
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "123456"})
    return github._get_gh_headers()


def test_update_pr_status(expected_headers, mocker):
    request = mocker.patch.object(github.requests, "post", return_value=None)

    github.update_pr_status("url", "state", "context", "description")

    request.assert_called_once_with(
        "url",
        json={"context": "context", "state": "state", "description": "description"},
        headers=expected_headers,
    )


def test_get_commits(expected_headers, mocker):
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "123456"})
    request = mocker.patch.object(github.requests, "get", return_value=MagicMock())

    github.get_commits("url")

    request.assert_called_once_with("url", headers=expected_headers)


def test_write_standard_summary(expected_headers, mocker):
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "123456"})
    mocker.patch.object(
        github.summary_factory, "create_standard_summary", return_value="content"
    )
    request = mocker.patch.object(github.requests, "post", return_value=MagicMock())

    github.write_standard_summary("url", [])

    request.assert_called_once_with(
        "url", json={"body": "content"}, headers=expected_headers
    )


def test_get_open_prs(expected_headers, mocker):
    request = mocker.patch.object(github.requests, "get", return_value=MagicMock())

    github.get_open_prs("guilatrova/examplerepo")

    request.assert_called_once_with(
        "https://api.github.com/repos/guilatrova/examplerepo/pulls?state=open",
        headers=expected_headers,
    )
