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


def test_extract_pr_data():
    dto = CircleCommitDTO("", "", "", "", "", "", pr_link="https://github.com/owner-here/project-here/pull/200")
    results = dto._extract_pr_data()

    assert len(results) == 3
    assert results["owner"] == "owner-here"
    assert results["project"] == "project-here"
    assert results["pr_number"] == "200"


def test_get_pr_urls():
    dto = CircleCommitDTO("owner-here", "project-here", "commit-hash", "", "", "",
                            pr_link="https://github.com/owner-here/project-here/pull/200")
    urls = dto.get_pr_urls()

    assert len(urls) == 2
    assert (
        urls[0]
        == "https://api.github.com/repos/owner-here/project-here/issues/200/comments"
    )
    assert (
        urls[1]
        == "https://api.github.com/repos/owner-here/project-here/statuses/commit-hash"
    )

