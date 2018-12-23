import os

import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = os.environ.get("BUCKET_NAME", "ci-quality-reports")


def _get_file(prefix, hash):
    s3 = boto3.client("s3")

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=f"{prefix}/{hash}")
    except ClientError as ex:
        if ex.response["Error"]["Code"] == "NoSuchKey":
            return False
        else:
            raise
    else:
        return response["Body"].read().decode("utf-8")


def get_coverage_file(hash):
    return _get_file("coverage", hash)


def get_quality_file(hash):
    return _get_file("quality", hash)
