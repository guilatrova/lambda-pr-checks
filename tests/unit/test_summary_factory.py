import os

from src import quality_summary, summary_factory


def test_create_standard_summary(mocker):
    mocker.patch.dict(os.environ, {"DOCS_STANDARD_LINK": "companystandard.com"})
    commits = [
        {"standard": True, "sha": "123456789", "message": "Message"},
        {"standard": False, "sha": "123456789", "message": "Message 2"},
    ]

    actual = summary_factory.create_standard_summary(commits)
    assert "diff" in actual
    assert "+ 1234567 Message\n" in actual
    assert "- 1234567 Message 2\n" in actual
    assert "[docs](companystandard.com)" in actual
    assert "#PLACEHOLDER#" not in actual
    assert "#DOCS#" not in actual


def test_create_coverage_summary(mocker, covdiff_content):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiff_content
    )

    report = quality_summary._read_coverage_file("")

    result = summary_factory.create_coverage_summary(report, "footer_message")

    # General
    assert "## Coverage Report" in result
    assert "origin/dev" in result
    assert "footer_message" in result
    assert "\n+ Covered lines" in result
    assert "\n- Missing lines" in result
    assert "\n+ Coverage" in result
    assert "85 \n" in result
    assert "72 \n" in result
    assert "15% \n" in result

    # Content
    assert "\n...dels/worker/feedback/models.py  60.0% " in result
    assert "\nexample/schemas/subjects.py        25.0% " in result


def test_create_quality_summary(mocker, qualitydiff_content):
    mocker.patch.object(
        quality_summary.s3, "get_quality_file", return_value=qualitydiff_content
    )

    report = quality_summary._read_quality_file("")

    result = summary_factory.create_quality_summary(report, "footer_message")

    # General
    assert "## Quality Report" in result
    assert "origin/dev" in result
    assert "footer_message" in result
    assert "\n+ Total lines" in result
    assert "\n- Violation lines" in result
    assert "\n+ Quality" in result
    assert "589 \n" in result
    assert "5 \n" in result
    assert "99% \n" in result

    # Content
    assert "\n...ple/workers/feedback/models.py  80.0% " in result
    assert "\nexample/schemas/subjects.py        83.3% " in result


def test_create_empty_coverage_summary():
    result = summary_factory.create_coverage_summary(False, "footer_message")
    assert result == ""


def test_create_empty_quality_summary():
    result = summary_factory.create_quality_summary(False, "footer_message")
    assert result == ""