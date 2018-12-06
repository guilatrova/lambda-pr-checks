import json
import os
from collections import namedtuple

import pytest
from src import pr_standard


@pytest.fixture()
def incoming_github_payload():
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "../../src/pr_standard.json")
    with open(file_path) as data:
        return data


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
    pass
    # requests_response_mock = namedtuple("response", ["text"])
    # requests_response_mock.text = "1.1.1.1\n"

    # request_mock = mocker.patch.object(
    #     app.requests, "get", side_effect=requests_response_mock
    # )

    # ret = app.lambda_handler(apigw_event, "")
    # assert ret["statusCode"] == 200

    # for key in ("message", "location"):
    #     assert key in ret["body"]

    # data = json.loads(ret["body"])
    # assert data["message"] == "hello world"
