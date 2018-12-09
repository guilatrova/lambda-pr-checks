import json
import logging
import traceback

try:
    import github
except ModuleNotFoundError:
    from . import github  # For tests

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

GH_FAIL_RESPONSE = {"statusCode": 500, "headers": {"Content-Type": "application/json"}}
SLACK_FAIL_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
}


def create_slack_error_message(text):
    return {**SLACK_FAIL_RESPONSE, "body": {"response_type": "ephemeral", "text": text}}


def get_error_response(integration, details):
    if integration == "github":
        return {**GH_FAIL_RESPONSE, "body": json.dumps(details)}

    # Slack
    def append(original, key):
        return f"{original}\n*{key}:* {details[key]}"

    text = ""
    for key in details.keys():
        text = append(text, key)

    return create_slack_error_message(text)


def error_handler(integration):
    def outer_wrapper(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except github.GitHubException as ghex:
                logging.error("GitHubException catch by wrapper")
                body = {
                    "type": "github",
                    "exception": repr(ghex),
                    "stacktrace": traceback.format_exc(),
                    "url_requested": ghex.url,
                    "gh_response": ghex.response_text,
                }

                logging.error("GitHubException Details: " + str(body))
                return get_error_response(integration, body)

            except Exception as ex:
                logging.error("Exception catch by wrapper")
                body = {
                    "type": "unknown",
                    "exception": repr(ex),
                    "stacktrace": traceback.format_exc(),
                }

                logging.error("Exception Details: " + str(body))
                return get_error_response(integration, body)

        return wrapper

    return outer_wrapper
