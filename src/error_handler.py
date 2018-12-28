import json
import logging
import sys
import traceback

try:
    from thirdparties import github
except ModuleNotFoundError:
    from .thirdparties import github  # For tests

logger = logging.getLogger()

GH_FAIL_RESPONSE = {"statusCode": 500, "headers": {"Content-Type": "application/json"}}
SLACK_FAIL_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
}


def create_slack_error_message(text):
    body = json.dumps({"response_type": "ephemeral", "text": text})
    return {**SLACK_FAIL_RESPONSE, "body": body}


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


def wrapper_for(integration):
    def _outer_wrapper(func):
        def _inner_wrapper(event, *args, **kwargs):
            logging.info("Error handler attached")
            body = event.get("body")
            logging.info(f"Incoming payload: {body}")

            try:
                return func(event, *args, **kwargs)

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

            except:
                logging.error("Exception catch by wrapper")
                body = {
                    "type": "unknown",
                    "exception": repr(sys.exc_info()[0]),
                    "stacktrace": traceback.format_exc(),
                }

                logging.error("Exception Details: " + str(body))
                return get_error_response(integration, body)

        return _inner_wrapper

    return _outer_wrapper
