import os

from src import codefreezer


def test_extract_command(incoming_slack_command):
    output = codefreezer._extract_command(incoming_slack_command)

    assert output["command"] == "/codefreeze"
    assert output["user_name"] == "Guilherme"
    assert output["channel_name"] == "test"


def test_extract_command_process_args(incoming_slack_command):
    output = codefreezer._extract_command(incoming_slack_command)

    assert output["text"] == "enable"
    assert output["args"] == ["Jan", "20"]


def test_enable_freeze(mocker):
    repos = "guilatrova/examplerepo"
    prs = [{"statuses_url": "correct_url"}]

    mocker.patch.dict(os.environ, {"REPOS": repos})
    open_pr_mock = mocker.patch.object(
        codefreezer.github, "get_open_prs", return_value=prs
    )
    update_pr_mock = mocker.patch.object(
        codefreezer.github, "update_pr_status", return_value=True
    )
    write_db_mock = mocker.patch.object(
        codefreezer.dynamodb, "write_config", return_value=None
    )

    codefreezer._freeze({"text": "enable", "user_name": "guilherme"})
    open_pr_mock.assert_called_once_with(repos)
    update_pr_mock.assert_called_once_with(
        "correct_url", "failure", "CodeFreeze", codefreezer.CODE_FREEZE_ENABLED_MESSAGE
    )
    write_db_mock.assert_called_once_with(
        codefreezer.dynamodb.FREEZE_CONFIG, Status="enabled", Author="guilherme"
    )


def test_disable_freeze(mocker):
    repos = "guilatrova/examplerepo"
    prs = [{"statuses_url": "correct_url"}]

    mocker.patch.dict(os.environ, {"REPOS": repos})
    open_pr_mock = mocker.patch.object(
        codefreezer.github, "get_open_prs", return_value=prs
    )
    update_pr_mock = mocker.patch.object(
        codefreezer.github, "update_pr_status", return_value=True
    )
    write_db_mock = mocker.patch.object(
        codefreezer.dynamodb, "write_config", return_value=None
    )

    codefreezer._freeze({"text": "disable", "user_name": "guilherme"})
    open_pr_mock.assert_called_once_with(repos)
    update_pr_mock.assert_called_once_with("correct_url", "success", "CodeFreeze", "")
    write_db_mock.assert_called_once_with(
        codefreezer.dynamodb.FREEZE_CONFIG, Status="disabled", Author="guilherme"
    )


def test_handler_calls_correct_functions(event_creator, incoming_slack_command, mocker):
    freeze_mock = mocker.patch.object(codefreezer, "_freeze", return_value=None)
    event = event_creator(incoming_slack_command)

    command = codefreezer._extract_command(incoming_slack_command)
    response = codefreezer.handler(event, "")

    freeze_mock.assert_called_once_with(command)
    assert response["statusCode"] == 200
