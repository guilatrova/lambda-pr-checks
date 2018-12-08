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


def test_write_error_summary(expected_headers, mocker):
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "123456"})
    mocker.patch.object(github, "_create_summary_content", return_value="content")
    request = mocker.patch.object(github.requests, "post", return_value=MagicMock())

    github.write_error_summary("url", [])

    request.assert_called_once_with(
        "url", json={"body": "content"}, headers=expected_headers
    )


def test_create_summary_content(mocker):
    mocker.patch.dict(os.environ, {"DOCS_STANDARD_LINK": "companystandard.com"})
    commits = [
        {"standard": True, "sha": "123456789", "message": "Message"},
        {"standard": False, "sha": "123456789", "message": "Message 2"},
    ]

    actual = github._create_summary_content(commits)
    assert "diff" in actual
    assert "+ 1234567 Message\n" in actual
    assert "- 1234567 Message 2\n" in actual
    assert "[docs](companystandard.com)" in actual
    assert "#PLACEHOLDER#" not in actual
    assert "#DOCS#" not in actual
