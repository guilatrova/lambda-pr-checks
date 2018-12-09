from unittest.mock import MagicMock

from src import dynamodb


def test_get_empty_code_freeze_config(mocker):
    table_mock = MagicMock(get_item=MagicMock(return_value={}))
    mocker.patch.object(dynamodb, "_get_table", return_value=table_mock)

    response = dynamodb.get_code_freeze_config()

    assert "ConfigName" in response
    assert "Status" in response
    assert "Author" in response
