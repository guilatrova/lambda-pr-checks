from urllib.parse import parse_qs

OK_RESPONSE = {"statusCode": 200, "headers": {"Content-Type": "text/plain"}}


def _extract_command(raw):
    result = {}
    parsed = parse_qs(raw)

    for key, value in parsed.items():
        result[key] = value[0].strip()

    text = result["text"].split()
    result["text"] = text[0]
    result["args"] = text[1:]

    return result


def handler(event, context):
    slack_command = _extract_command(event.get("body"))

    return {
        **OK_RESPONSE,
        "body": "You're really called " + slack_command["user_name"][0],
    }
