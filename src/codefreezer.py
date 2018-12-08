from urllib.parse import parse_qs

OK_RESPONSE = {"statusCode": 200, "headers": {"Content-Type": "text/plain"}}


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


def _freeze(command):
    pass


def handler(event, context):
    slack_command = _extract_command(event.get("body"))

    if slack_command["text"] == "enable":
        _freeze(slack_command)

    return {**OK_RESPONSE, "body": "ok"}
