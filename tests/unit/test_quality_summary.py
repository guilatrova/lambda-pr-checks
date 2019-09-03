import json
from unittest.mock import call

from src import quality_summary
from src.CircleCommitDTO import CircleCommitDTO



def test_read_coverage_file(mocker, covdiff_content):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiff_content
    )

    report = quality_summary._read_coverage_file("")

    assert len(report["files"]) == 5
    assert len(report["files"][0]) == 3

    assert report["files"][0]["file"] == "example/models/worker/feedback/models.py"
    assert report["files"][0]["value"] == "60.0%"
    assert report["files"][0]["missing"] == ": Missing lines 24-25"

    assert report["files"][4]["file"] == "tests/full/test_submission.py"
    assert report["files"][4]["value"] == "100%"
    assert report["files"][4]["missing"] is False

    assert report["target_branch"] == "origin/dev"
    assert report["total"] == "85"
    assert report["missing"] == "72"
    assert report["coverage"] == "15%"


def test_read_coverage_file_single_line(mocker, covdiffsingle_content):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiffsingle_content
    )

    report = quality_summary._read_coverage_file("")

    assert report["total"] == "1"
    assert report["missing"] == "1"


def test_read_coverage_empty_file(mocker, covdiff_empty_content):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiff_empty_content
    )

    report = quality_summary._read_coverage_file("")

    assert report is False


def test_update_github_status_failure(mocker):
    update_status_mock = mocker.patch.object(quality_summary.github, "update_pr_status")
    report = {"key": "30%"}

    quality_summary._update_github_status(report, "url", "key", 50, "link")

    update_status_mock.assert_called_once_with(
        "url", "failure", "FineTune Key", "Key diff is below expected (30% out of 50%)", "link"
    )


def test_update_github_status_success(mocker):
    update_status_mock = mocker.patch.object(quality_summary.github, "update_pr_status")
    report = {"key": "50%"}

    quality_summary._update_github_status(report, "url", "key", 50, "link")

    update_status_mock.assert_called_once_with(
        "url", "success", "FineTune Key", "Key diff is good!", "link"
    )


def test_update_github_status_no_report(mocker):
    update_status_mock = mocker.patch.object(quality_summary.github, "update_pr_status")

    quality_summary._update_github_status(False, "url", "coverage", 50, "link")

    update_status_mock.assert_called_once_with(
        "url", "success", "FineTune Coverage", "No report provided for this commit", ""
    )


def test_update_status_summary_all_successful_reports(mocker):
    # Arrange
    cov_report = {"coverage": "100%"}
    quality_report = {"quality": "100%"}
    footers = {"quality": "quality", "coverage": "coverage"}
    status_url = "status_url"
    summary_url = "summary_url"
    cov_link = "https://build-repo-gh.circle-artifacts.com/0/quality-reports/coverage.html"
    qual_link = "https://build-repo-gh.circle-artifacts.com/0/quality-reports/eslint.html"

    write_summary_mock = mocker.patch.object(
        quality_summary.github, "write_quality_summary"
    )
    update_status_mock = mocker.patch.object(quality_summary.github, "update_pr_status")

    # Act
    report_links = CircleCommitDTO("owner", "project", "commit", "build", "qualitytool", "repo").get_reports_links()
    quality_summary._update_github_pr(
        summary_url, status_url, cov_report, quality_report, footers, report_links, "eslint"
    )
    write_summary_mock.assert_called_once_with(
        summary_url, cov_report, quality_report, footers["coverage"], footers["quality"]
    )

    # Assert
    assert update_status_mock.call_count == 2
    coverage_call = call(
        status_url, "success", "FineTune Coverage", "Coverage diff is good!", cov_link
    )
    quality_call = call(
        status_url, "success", "FineTune Quality", "Quality diff is good!", qual_link
    )
    update_status_mock.assert_has_calls([coverage_call, quality_call])
