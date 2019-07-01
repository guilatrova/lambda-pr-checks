import json
from unittest.mock import call

from src import quality_summary


def check_report_url(reports, key, file):
    assert "circle-artifacts" in reports[key]["url"]
    assert file in reports[key]["url"]


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


def test_read_quality_file(mocker, qualitydiff_content):
    mocker.patch.object(
        quality_summary.s3, "get_quality_file", return_value=qualitydiff_content
    )

    report = quality_summary._read_quality_file("")

    # Issues
    assert len(report["issues"]) == 7
    assert len(report["issues"][0]) == 4

    # Issue in-depth
    assert report["issues"][0]["file"] == "example/workers/feedback/models.py"
    assert report["issues"][0]["line"] == "3"
    assert report["issues"][0]["error_code"] == "F401"
    assert (
        report["issues"][0]["description"] == "'sqlalchemy.String' imported but unused"
    )

    # Files
    assert len(report["files"]) == 13
    assert len(report["files"][0]) == 2

    # Files in-depth
    assert report["files"][0]["file"] == "example/workers/feedback/models.py"
    assert report["files"][0]["value"] == "80.0%"

    # Overall
    assert report["target_branch"] == "origin/dev"
    assert report["total"] == "589"
    assert report["violations"] == "5"
    assert report["quality"] == "99%"


def test_read_quality_file_single_line(mocker, qualitydiffsingle_content):
    mocker.patch.object(
        quality_summary.s3, "get_quality_file", return_value=qualitydiffsingle_content
    )

    report = quality_summary._read_quality_file("")

    assert report["total"] == "1"
    assert report["violations"] == "1"


def test_read_quality_empty_file(mocker, qualitydiff_empty_content):
    mocker.patch.object(
        quality_summary.s3, "get_quality_file", return_value=qualitydiff_empty_content
    )

    report = quality_summary._read_quality_file("")

    assert report is False


def test_get_reports_link(mocker, ci_artifacts_payload):
    reports = quality_summary._get_reports_link("", "", "", "")

    assert len(reports.keys()) == 2
    check_report_url(reports, "flake8", "flake8.html")
    check_report_url(reports, "coverage", "coverage.html")


def test_extract_pr_data():
    results = quality_summary._extract_pr_data(
        "https://github.com/owner-here/repository-here/pull/200"
    )

    assert len(results) == 3
    assert results["owner"] == "owner-here"
    assert results["repo"] == "repository-here"
    assert results["pr_number"] == "200"


def test_get_pr_urls():
    urls = quality_summary._get_pr_urls(
        "https://github.com/owner-here/repository-here/pull/200", "commit-hash"
    )

    assert len(urls) == 2
    assert (
        urls[0]
        == "https://api.github.com/repos/owner-here/repository-here/issues/200/comments"
    )
    assert (
        urls[1]
        == "https://api.github.com/repos/owner-here/repository-here/statuses/commit-hash"
    )


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
    qual_link = "https://build-repo-gh.circle-artifacts.com/0/quality-reports/flake8.html"

    write_summary_mock = mocker.patch.object(
        quality_summary.github, "write_quality_summary"
    )
    update_status_mock = mocker.patch.object(quality_summary.github, "update_pr_status")

    # Act
    report_links = quality_summary._get_reports_link("owner", "project", "build", "repo")
    quality_summary._update_github_pr(
        summary_url, status_url, cov_report, quality_report, footers, report_links
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
