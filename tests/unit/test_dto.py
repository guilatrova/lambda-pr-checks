from src.CircleCommitDTO import CircleCommitDTO


def check_report_url(reports, key, file):
    assert "circle-artifacts" in reports[key]["url"]
    assert file in reports[key]["url"]


def test_get_reports_link(mocker, ci_artifacts_payload):
    dto = CircleCommitDTO("", "", "", "", "", "")
    reports = dto.get_reports_links()

    assert len(reports.keys()) == 3
    check_report_url(reports, "eslint", "eslint.html")
    check_report_url(reports, "flake8", "flake8.html")
    check_report_url(reports, "coverage", "coverage.html")
