import hashlib
import hmac
import json
import logging
import os

logger = logging.getLogger()

INVALID_SIGNATURE_RESPONSE = {
    "statusCode": 404
}

def _get_secret():
    raw = os.environ.get("LAMBDA_SECRET", "secretless")
    return raw.encode()

def validate_secret(signature, body):
    secret = _get_secret()

    if not signature:
        logger.error("No signature found")
        return False

    sha_name, signature = signature.split('=')
    if sha_name != 'sha1':
        logger.error("Signature not signed with sha1")
        return False

    mac = hmac.new(secret, msg=body, digestmod=hashlib.sha1)

    expected = str(mac.hexdigest())
    received = str(signature)

    matches = hmac.compare_digest(expected, received)
    if not matches:
        logger.error(f"Signature ({received}) does not match expected ({expected})")
        return False

    return True

def secret_handler(func):
    def _wrapper(event, *args, **kwargs):
        print("Secret handler attached")

        signature = event.get('headers', {}).get('X-Hub-Signature', '')
        body = event.get('body')

        if validate_secret(signature, body):
            return func(event, *args, **kwargs)

        return INVALID_SIGNATURE_RESPONSE

    return _wrapper
