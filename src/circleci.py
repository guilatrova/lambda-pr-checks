import os

import requests


def get_artifacts_from_build(owner, project, build_num):
    TOKEN = os.environ.get("CIRCLECI_TOKEN")
    response = requests.get(
        f"https://circleci.com/api/v1.1/project/github/{owner}/{project}/{build_num}/artifacts?circle-token={TOKEN}"
    )

    return response.json()
