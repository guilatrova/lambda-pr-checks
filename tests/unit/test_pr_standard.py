import json
from unittest.mock import MagicMock

from src import error_handler, pr_standard


def check_commits(result, valid, *args):
    actual_result, commits = result

    assert actual_result == valid
    assert len(commits) == len(args)

    for i in range(len(args)):
        assert commits[i]["standard"] == args[i]


def test_invalid_pr_title():
    assert pr_standard._validate_title("Improved scripts") is False


def test_valid_title_no_ticket():
    assert pr_standard._validate_title("NO-TICKET Improved scripts") is True


def test_valid_title_with_ticket_ids():
    assert pr_standard._validate_title("FY-1234 Jira Ticket") is True
    assert pr_standard._validate_title("FTL-8721 Backlog Ticket") is True
    assert pr_standard._validate_title("COM-7789 Jira Ticket") is True
    assert pr_standard._validate_title("ABC-2222 Random ticket") is True


def test_valid_commits(valid_commits, mocker):
    mocker.patch.object(pr_standard.github, "get_commits", return_value=valid_commits)
    result = pr_standard._validate_commits({"commits_url": ""})
    check_commits(result, True, True, True)


def test_valid_commits_git_merge(valid_commits, mocker):
    valid_commits.append({"sha": "789", "commit": {"message": "Merge pull request"}})
    mocker.patch.object(pr_standard.github, "get_commits", return_value=valid_commits)
    result = pr_standard._validate_commits({"commits_url": ""})
    check_commits(result, True, True, True, True)


def test_invalid_commits(valid_commits, mocker):
    mocker.patch.object(pr_standard.github, "get_commits", return_value=valid_commits)
    valid_commits.append(
        {
            "sha": "901",
            "commit": {"message": "Did some work with an invalid commit message"},
        }
    )
    result = pr_standard._validate_commits({"commits_url": ""})
    check_commits(result, False, True, True, False)


def test_lambda_handler(event_creator, incoming_open_pr_payload, mocker):
    event = event_creator(incoming_open_pr_payload)
    github_payload = json.loads(event["body"])
    update_pr_status_mock = mocker.patch.object(
        pr_standard.github, "update_pr_status", return_value=MagicMock(ok=True)
    )
    mocker.patch.object(pr_standard, "_validate_title", return_value=True)
    mocker.patch.object(pr_standard, "_validate_commits", return_value=(True, []))
    error_summary_mock = mocker.patch.object(
        pr_standard.github, "write_error_summary", return_value=MagicMock()
    )

    response = pr_standard.handler(event, "")

    update_pr_status_mock.assert_called_once_with(
        github_payload["pull_request"]["statuses_url"],
        "success",
        "PR standard",
        pr_standard.SUCCESS_MESSAGE,
    )

    assert response == pr_standard.OK_RESPONSE
    assert error_summary_mock.called is False


def test_lambda_handler_invalid_pr_title(
    event_creator, incoming_open_pr_payload, mocker
):
    event = event_creator(incoming_open_pr_payload)
    github_payload = json.loads(event["body"])
    update_pr_status_mock = mocker.patch.object(
        pr_standard.github, "update_pr_status", return_value=MagicMock(ok=True)
    )
    mocker.patch.object(pr_standard, "_validate_title", return_value=False)
    error_summary_mock = mocker.patch.object(
        pr_standard.github, "write_error_summary", return_value=MagicMock()
    )

    response = pr_standard.handler(event, "")

    update_pr_status_mock.assert_called_once_with(
        github_payload["pull_request"]["statuses_url"],
        "failure",
        "PR standard",
        pr_standard.PR_TITLE_FAILURE_MESSAGE,
    )

    assert response == pr_standard.OK_RESPONSE
    assert error_summary_mock.called is False


def test_lambda_handler_invalid_commits(
    event_creator, incoming_open_pr_payload, mocker
):
    event = event_creator(incoming_open_pr_payload)
    github_payload = json.loads(event["body"])
    commits_analyzed = [{}, {}]

    update_pr_status_mock = mocker.patch.object(
        pr_standard.github, "update_pr_status", return_value=MagicMock(ok=True)
    )
    mocker.patch.object(
        pr_standard,
        "_validate_pr",
        return_value=(False, pr_standard.PR_COMMITS_FAILURE_MESSAGE, commits_analyzed),
    )
    error_summary_mock = mocker.patch.object(
        pr_standard.github, "write_error_summary", return_value=MagicMock()
    )

    response = pr_standard.handler(event, "")

    update_pr_status_mock.assert_called_once_with(
        github_payload["pull_request"]["statuses_url"],
        "failure",
        "PR standard",
        pr_standard.PR_COMMITS_FAILURE_MESSAGE,
    )

    error_summary_mock.assert_called_once_with(
        github_payload["pull_request"]["comments_url"], commits_analyzed
    )

    assert response == pr_standard.OK_RESPONSE


def test_lambda_handler_handles_exception(
    event_creator, incoming_open_pr_payload, mocker
):
    event = event_creator(incoming_open_pr_payload)

    mocker.patch.object(pr_standard, "_validate_title", return_value=True)
    mocker.patch.object(pr_standard, "_validate_commits", return_value=(True, []))
    mocker.patch.object(
        pr_standard.github,
        "update_pr_status",
        side_effect=pr_standard.github.GitHubException("www.site.com", "text"),
    )

    response = pr_standard.handler(event, "")

    assert response["statusCode"] == error_handler.GH_FAIL_RESPONSE["statusCode"]
    assert response["headers"] == error_handler.GH_FAIL_RESPONSE["headers"]
    assert "body" in response
