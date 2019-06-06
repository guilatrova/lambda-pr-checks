from src import quality_summary


def test_flake8_read_quality_file(mocker, flake8_qualitydiff_content):
    mocker.patch.object(quality_summary.s3, "get_quality_file", return_value=flake8_qualitydiff_content)

    report = quality_summary._read_quality_file("")

    # Issues
    assert len(report["issues"]) == 7
    assert len(report["issues"][0]) == 4

    # Issue in-depth
    assert report["issues"][0]["file"] == "example/workers/feedback/models.py"
    assert report["issues"][0]["line"] == "3"
    assert report["issues"][0]["error_code"] == "F401"
    assert report["issues"][0]["description"] == "'sqlalchemy.String' imported but unused"

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


def test_flake8_read_quality_file_single_line(mocker, flake8_qualitydiffsingle_content):
    mocker.patch.object(quality_summary.s3, "get_quality_file", return_value=flake8_qualitydiffsingle_content)

    report = quality_summary._read_quality_file("")

    assert report["total"] == "1"
    assert report["violations"] == "1"


def test_flake8_read_quality_empty_file(mocker, flake8_qualitydiff_empty_content):
    mocker.patch.object(quality_summary.s3, "get_quality_file", return_value=flake8_qualitydiff_empty_content)

    report = quality_summary._read_quality_file("")

    assert report is False


def test_flake8_read_quality_file(mocker, flake8_qualitydiff_content):
    mocker.patch.object(quality_summary.s3, "get_quality_file", return_value=flake8_qualitydiff_content)

    report = quality_summary._read_quality_file("")

    # Issues
    assert len(report["issues"]) == 7
    assert len(report["issues"][0]) == 4

    # Issue in-depth
    assert report["issues"][0]["file"] == "example/workers/feedback/models.py"
    assert report["issues"][0]["line"] == "3"
    assert report["issues"][0]["error_code"] == "F401"
    assert report["issues"][0]["description"] == "'sqlalchemy.String' imported but unused"

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
