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


def test_handler_calls_correct_functions(event_creator, incoming_slack_command, mocker):
    freeze_mock = mocker.patch.object(codefreezer, "_freeze", return_value=None)
    event = event_creator(incoming_slack_command)

    command = codefreezer._extract_command(incoming_slack_command)
    response = codefreezer.handler(event, "")

    freeze_mock.assert_called_once_with(command)
    assert response["statusCode"] == 200
