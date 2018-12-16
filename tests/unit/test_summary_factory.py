import os

from src import summary_factory


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
