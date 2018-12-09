import os
from urllib.parse import parse_qs

try:
    import github
    import dynamodb
except ModuleNotFoundError:  # For tests
    from src import github
    from src import dynamodb

OK_RESPONSE = {"statusCode": 200, "headers": {"Content-Type": "text/plain"}}
CODE_FREEZE_ENABLED_MESSAGE = (
    "A merge is currently blocked because a Code Freeze is enabled"
)


def _extract_command(raw):
    result = {}
    parsed = parse_qs(raw)

    for key, value in parsed.items():
        result[key] = value[0].strip()

    # Handle text to separate main text from args
    text = result["text"].split()
    result["text"] = text[0]
    result["args"] = text[1:]

    return result


def _status():
    config = dynamodb.get_code_freeze_config()
    author = config["Author"]

    def _create_response(status, emoji, author):
        return {
            "text": f"Code Freeze is currently *{status}* :{emoji}:",
            "attachments": [{"text": f"Author: {author}"}],
        }

    if config["Status"] == "enabled":
        return _create_response("enabled", "snowflake", author)
    else:
        return _create_response("disabled", "fire", author)


def _freeze(command):
    if command["text"] == "enable":
        pr_state = "failure"
        status = "enabled"
        description = CODE_FREEZE_ENABLED_MESSAGE
    else:
        pr_state = "success"
        status = "disabled"
        description = ""

    dynamodb.write_config(
        dynamodb.FREEZE_CONFIG, Status=status, Author=command["user_name"]
    )
    # expects to be in format: owner/repo1,owner/repo2
    repos = os.environ.get("REPOS", []).split()

    for repo in repos:
        prs = github.get_open_prs(repo)

        for pr in prs:
            github.update_pr_status(
                pr["statuses_url"], pr_state, "CodeFreeze", description
            )


def handler(event, context):
    slack_command = _extract_command(event.get("body"))

    if slack_command["text"] == "enable":
        _freeze(slack_command)

    return {**OK_RESPONSE, "body": "ok"}
