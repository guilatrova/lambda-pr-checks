from src import quality_summary


def test_github_pullrequest(event_creator, incoming_open_pr_payload, mocker):
    event = event_creator(incoming_open_pr_payload)
    response = quality_summary.gh_handler(event, None)

    assert response["statusCode"] == 200
