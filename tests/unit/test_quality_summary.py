from src import quality_summary


def test_read_coverage_file(mocker, covdiff_content):
    mocker.patch.object(
        quality_summary.s3, "get_coverage_file", return_value=covdiff_content
    )

    matches = quality_summary._read_coverage_file("")

    assert len(matches) == 4
    assert len(matches[0]) == 3

    assert matches[0][0] == "example/worker/feedback/models.py"
    assert matches[0][1] == "60.0%"
    assert matches[0][2] == ": Missing lines 24-25"
