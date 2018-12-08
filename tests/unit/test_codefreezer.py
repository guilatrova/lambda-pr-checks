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
