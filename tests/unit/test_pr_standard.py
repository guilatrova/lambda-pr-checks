import json
import os
from unittest.mock import MagicMock

from src import github, pr_standard


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
    assert pr_standard._validate_commits({"commits_url": ""}) is True


def test_valid_commits_git_merge(valid_commits, mocker):
    valid_commits.append({"sha": "789", "commit": {"message": "Merge pull request"}})
    mocker.patch.object(pr_standard.github, "get_commits", return_value=valid_commits)
    assert pr_standard._validate_commits({"commits_url": ""}) is True


def test_invalid_commits(valid_commits, mocker):
    mocker.patch.object(pr_standard.github, "get_commits", return_value=valid_commits)
    valid_commits.append(
        {
            "sha": "901",
            "commit": {"message": "Did some work with an invalid commit message"},
        }
    )
    assert pr_standard._validate_commits({"commits_url": ""}) is False


def test_lambda_handler(event_creator, incoming_open_pr_payload, mocker):
    event = event_creator(incoming_open_pr_payload)
    github_payload = json.loads(event["body"])
    update_pr_status_mock = mocker.patch.object(
        pr_standard.github, "update_pr_status", return_value=MagicMock(ok=True)
    )
    mocker.patch.object(pr_standard, "_validate_title", return_value=True)
    mocker.patch.object(pr_standard, "_validate_commits", return_value=True)

    response = pr_standard.handler(event, "")

    update_pr_status_mock.assert_called_once_with(
        github_payload["pull_request"]["statuses_url"],
        "success",
        "PR standard",
        pr_standard.SUCCESS_MESSAGE,
    )

    assert response == pr_standard.OK_RESPONSE


def test_lambda_handler_invalid_pr(event_creator, incoming_open_pr_payload, mocker):
    event = event_creator(incoming_open_pr_payload)
    github_payload = json.loads(event["body"])
    update_pr_status_mock = mocker.patch.object(
        pr_standard.github, "update_pr_status", return_value=MagicMock(ok=True)
    )
    mocker.patch.object(pr_standard, "_validate_title", return_value=False)

    response = pr_standard.handler(event, "")

    update_pr_status_mock.assert_called_once_with(
        github_payload["pull_request"]["statuses_url"],
        "failure",
        "PR standard",
        pr_standard.PR_TITLE_FAILURE_MESSAGE,
    )

    assert response == pr_standard.OK_RESPONSE


def test_lambda_handler_failing_gh_hook(
    event_creator, incoming_open_pr_payload, mocker
):
    event = event_creator(incoming_open_pr_payload)
    gh_error = json.dumps({"text": "A crazy error just happened"})

    mocker.patch.object(pr_standard, "_validate_title", return_value=True)
    mocker.patch.object(pr_standard, "_validate_commits", return_value=True)
    mocker.patch.object(
        pr_standard.github,
        "update_pr_status",
        return_value=MagicMock(ok=False, text=gh_error),
    )

    response = pr_standard.handler(event, "")

    assert response["statusCode"] == pr_standard.FAIL_RESPONSE["statusCode"]
    assert response["headers"] == pr_standard.FAIL_RESPONSE["headers"]
    assert "body" in response
    assert len(response["body"]) > 0
