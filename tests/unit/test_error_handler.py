import json

from src import error_handler


def test_create_slack_error_message():
    text = "simple text"

    result = error_handler.create_slack_error_message(text)

    assert result["statusCode"] == error_handler.SLACK_FAIL_RESPONSE["statusCode"]
    assert result["headers"] == error_handler.SLACK_FAIL_RESPONSE["headers"]
    assert "body" in result
    assert result["body"]["response_type"] == "ephemeral"
    assert result["body"]["text"] == text


def test_get_github_error_message():
    errors = {"key1": "desc1", "key2": "desc2"}

    result = error_handler.get_error_response("github", errors)

    assert result["statusCode"] == error_handler.GH_FAIL_RESPONSE["statusCode"]
    assert result["headers"] == error_handler.GH_FAIL_RESPONSE["headers"]
    assert "body" in result
    assert result["body"] == json.dumps(errors)


def test_get_slack_error_message():
    errors = {"key1": "desc1", "key2": "desc2"}

    result = error_handler.get_error_response("slack", errors)
    text = result["body"]["text"]

    assert text == "\n*key1:* desc1\n*key2:* desc2"
