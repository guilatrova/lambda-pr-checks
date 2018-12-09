import boto3

TABLE_NAME = "CodeFreezeConfig"
FREEZE_CONFIG = "FreezeStatus"
DEFAULT_STATUS = {"ConfigName": FREEZE_CONFIG, "Status": "disabled", "Author": ""}


def _get_table():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)
    return table


def write_config(key, **kwargs):
    table = _get_table()
    table.put_item(Item={"ConfigName": key, **kwargs})


def get_code_freeze_config():
    table = _get_table()
    response = table.get_item(Key={"ConfigName": FREEZE_CONFIG})

    if "Item" in response:
        return response["Item"]

    return DEFAULT_STATUS
