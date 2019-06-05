import re
from .base import BaseQualityAdapter


class Flake8Adapter(BaseQualityAdapter):
    def _process_content(self):
        report = {}

        matches = re.findall(r"(.*):(\d+): ([A-Z]\d+) (.*)", self.content)
        report["issues"] = [
            {"file": match[0], "line": match[1], "error_code": match[2], "description": match[3]} for match in matches
        ]

        matches = re.findall(r"(.*) \((.*)\)", self.content)
        report["files"] = [{"file": match[0], "value": match[1]} for match in matches]

        return report
