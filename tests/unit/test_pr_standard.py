import json
import os
from unittest.mock import MagicMock

import pytest

from src import pr_standard


@pytest.fixture()
def incoming_github_payload():
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "../payloads/pr_standard.json")
    with open(file_path) as data:
        return data.read()


@pytest.fixture()
def event_creator():
    def _generator(body):
        """ Generates API GW Event"""

        return {
            "body": body,
            "resource": "/{proxy+}",
            "requestContext": {
                "resourceId": "123456",
                "apiId": "1234567890",
                "resourcePath": "/{proxy+}",
                "httpMethod": "POST",
                "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
                "accountId": "123456789012",
                "identity": {
                    "apiKey": "",
                    "userArn": "",
                    "cognitoAuthenticationType": "",
                    "caller": "",
                    "userAgent": "Custom User Agent String",
                    "user": "",
                    "cognitoIdentityPoolId": "",
                    "cognitoIdentityId": "",
                    "cognitoAuthenticationProvider": "",
                    "sourceIp": "127.0.0.1",
                    "accountId": "",
                },
                "stage": "prod",
            },
            "queryStringParameters": {"foo": "bar"},
            "headers": {
                "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
                "Accept-Language": "en-US,en;q=0.8",
                "CloudFront-Is-Desktop-Viewer": "true",
                "CloudFront-Is-SmartTV-Viewer": "false",
                "CloudFront-Is-Mobile-Viewer": "false",
                "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
                "CloudFront-Viewer-Country": "US",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
                "X-Forwarded-Port": "443",
                "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
                "X-Forwarded-Proto": "https",
                "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
                "CloudFront-Is-Tablet-Viewer": "false",
                "Cache-Control": "max-age=0",
                "User-Agent": "Custom User Agent String",
                "CloudFront-Forwarded-Proto": "https",
                "Accept-Encoding": "gzip, deflate, sdch",
            },
            "pathParameters": {"proxy": "/examplepath"},
            "httpMethod": "POST",
            "stageVariables": {"baz": "qux"},
            "path": "/examplepath",
        }

    return _generator


def test_invalid_pr_title():
    assert pr_standard._validate_pr_title("Improved scripts") is False


def test_valid_title_no_ticket():
    assert pr_standard._validate_pr_title("NO-TICKET Improved scripts") is True


def test_valid_title_with_ticket_ids():
    assert pr_standard._validate_pr_title("FY-1234 Jira Ticket") is True
    assert pr_standard._validate_pr_title("FTL-8721 Backlog Ticket") is True
    assert pr_standard._validate_pr_title("COM-7789 Jira Ticket") is True
    assert pr_standard._validate_pr_title("ABC-2222 Random ticket") is True


def test_lambda_handler(event_creator, incoming_github_payload, mocker):
    event = event_creator(incoming_github_payload)
    github_payload = json.loads(event["body"])
    update_pr_status_mock = mocker.patch.object(
        pr_standard, "_update_pr_status", return_value=MagicMock(ok=True)
    )
    mocker.patch.object(pr_standard, "_validate_pr_title", return_value=True)

    response = pr_standard.handler(event, "")

    update_pr_status_mock.assert_called_once_with(
        github_payload["pull_request"]["statuses_url"],
        "success",
        "PR standard",
        "Your PR title is ok!",
    )

    assert response == pr_standard.OK_RESPONSE


def test_lambda_handler_invalid_pr(event_creator, incoming_github_payload, mocker):
    event = event_creator(incoming_github_payload)
    github_payload = json.loads(event["body"])
    update_pr_status_mock = mocker.patch.object(
        pr_standard, "_update_pr_status", return_value=MagicMock(ok=True)
    )
    mocker.patch.object(pr_standard, "_validate_pr_title", return_value=False)

    response = pr_standard.handler(event, "")

    update_pr_status_mock.assert_called_once_with(
        github_payload["pull_request"]["statuses_url"],
        "failure",
        "PR standard",
        "Your PR title should start with NO-TICKET or a ticket id",
    )

    assert response == pr_standard.OK_RESPONSE


def test_lambda_handler_failing_gh_hook(event_creator, incoming_github_payload, mocker):
    event = event_creator(incoming_github_payload)
    gh_error = json.dumps({"text": "A crazy error just happened"})

    mocker.patch.object(pr_standard, "_validate_pr_title", return_value=True)
    mocker.patch.object(
        pr_standard,
        "_update_pr_status",
        return_value=MagicMock(ok=False, text=gh_error),
    )

    response = pr_standard.handler(event, "")

    assert response["statusCode"] == pr_standard.FAIL_RESPONSE["statusCode"]
    assert response["headers"] == pr_standard.FAIL_RESPONSE["headers"]
    assert "body" in response
    assert len(response["body"]) > 0
