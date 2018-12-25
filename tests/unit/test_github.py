import os
from unittest.mock import MagicMock

import pytest

from src import github, quality_summary


@pytest.fixture()
def expected_headers(mocker):
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "123456"})
    return github._get_gh_headers()


@pytest.fixture()
def cov_report(covdiff_content, mocker):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiff_content
    )
    return quality_summary._read_coverage_file("")


@pytest.fixture()
def quality_report(qualitydiff_content, mocker):
    mocker.patch.object(
        quality_summary.s3, "get_quality_file", return_value=qualitydiff_content
    )
    return quality_summary._read_quality_file("")


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


def test_write_quality_summary_create_both_reports(
    mocker, cov_report, quality_report, expected_headers
):
    mocker.patch.object(github, "_get_comment_url", return_value=False)
    mocker.patch.object(
        github.summary_factory, "create_coverage_summary", return_value="covsummary"
    )
    mocker.patch.object(
        github.summary_factory, "create_quality_summary", return_value="quasummary"
    )
    post_mock = mocker.patch.object(github.requests, "post", side_effect=None)

    github.write_quality_summary("url", cov_report, quality_report, None, None)

    post_mock.assert_called_once_with(
        "url", json={"body": "covsummary\nquasummary"}, headers=expected_headers
    )


def test_write_quality_summary_update_both_reports(
    expected_headers, cov_report, quality_report, mocker
):
    mocker.patch.object(github, "_get_comment_url", return_value="edit_url")
    mocker.patch.object(
        github.summary_factory, "create_coverage_summary", return_value="covsummary"
    )
    mocker.patch.object(
        github.summary_factory, "create_quality_summary", return_value="quasummary"
    )
    patch_mock = mocker.patch.object(github.requests, "patch", side_effect=None)

    github.write_quality_summary("url", cov_report, quality_report, None, None)

    patch_mock.assert_called_once_with(
        "edit_url", json={"body": "covsummary\nquasummary"}, headers=expected_headers
    )


def test_write_quality_create_no_reports(expected_headers, mocker):
    mocker.patch.object(github, "_get_comment_url", return_value=False)

    post_mock = mocker.patch.object(github.requests, "post", side_effect=None)
    patch_mock = mocker.patch.object(github.requests, "patch", side_effect=None)
    delete_mock = mocker.patch.object(github.requests, "delete", side_effect=None)

    github.write_quality_summary("url", False, False, None, None)

    assert post_mock.called is False
    assert patch_mock.called is False
    assert delete_mock.called is False


def test_write_summary_deletes_report_previously_created(mocker, expected_headers):
    mocker.patch.object(github, "_get_comment_url", return_value="delete_url")
    delete_mock = mocker.patch.object(github.requests, "delete", side_effect=None)

    github.write_quality_summary("url", False, False, None, None)

    delete_mock.assert_called_once_with("delete_url", headers=expected_headers)
