import logging

import boto3

TABLE_NAME = "CodeFreezeConfig"
FREEZE_CONFIG = "FreezeStatus"
DEFAULT_STATUS = {"ConfigName": FREEZE_CONFIG, "Status": "disabled", "Author": ""}

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def _get_table():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)
    return table


def write_config(key, **kwargs):
    logger.info("Writing key: " + key)
    table = _get_table()
    table.put_item(Item={"ConfigName": key, **kwargs})


def get_code_freeze_config():
    table = _get_table()
    response = table.get_item(Key={"ConfigName": FREEZE_CONFIG})

    if "Item" in response:
        return response["Item"]

    return DEFAULT_STATUS
