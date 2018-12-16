import json

from src import quality_summary


def check_report_url(reports, key, file):
    assert "circle-artifacts" in reports[key]["url"]
    assert file in reports[key]["url"]


def test_read_coverage_file(mocker, covdiff_content):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiff_content
    )

    report = quality_summary._read_coverage_file("")

    assert len(report["files"]) == 4
    assert len(report["files"][0]) == 3

    assert report["files"][0][0] == "example/models/worker/feedback/models.py"
    assert report["files"][0][1] == "60.0%"
    assert report["files"][0][2] == ": Missing lines 24-25"

    assert report["target_branch"] == "origin/dev"
    assert report["total"] == "85"
    assert report["missing"] == "72"
    assert report["coverage"] == "15%"


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
    assert report["issues"][0][0] == "example/workers/feedback/models.py"
    assert report["issues"][0][1] == "3"
    assert report["issues"][0][2] == "F401"
    assert report["issues"][0][3] == "'sqlalchemy.String' imported but unused"

    # Files
    assert len(report["files"]) == 13
    assert len(report["files"][0]) == 2

    # Files in-depth
    assert report["files"][0][0] == "example/workers/feedback/models.py"
    assert report["files"][0][1] == "80.0%"

    # Overall
    assert report["target_branch"] == "origin/dev"
    assert report["total"] == "589"
    assert report["violations"] == "5"
    assert report["quality"] == "99%"


def test_read_quality_empty_file(mocker, qualitydiff_empty_content):
    mocker.patch.object(
        quality_summary.s3, "get_quality_file", return_value=qualitydiff_empty_content
    )

    report = quality_summary._read_quality_file("")

    assert report is False


def test_get_reports_link(mocker, ci_artifacts_payload):
    mocker.patch.object(
        quality_summary.circleci,
        "get_artifacts_from_build",
        return_value=json.loads(ci_artifacts_payload),
    )

    reports = quality_summary._get_reports_link("", "", "")

    assert len(reports.keys()) == 2
    check_report_url(reports, "flake8", "flake8.html")
    check_report_url(reports, "coverage", "coverage.html")
