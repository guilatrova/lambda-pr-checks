from src import quality_summary


def test_read_coverage_file(mocker, covdiff_content):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiff_content
    )

    report = quality_summary._read_coverage_file("")

    assert len(report["files"]) == 4
    assert len(report["files"][0]) == 3

    assert report["files"][0][0] == "example/worker/feedback/models.py"
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
