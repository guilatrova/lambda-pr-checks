import re

QUALITY_EMPTY_TEXT = "No lines with quality information in this diff."


class BaseQualityAdapter:
    def __init__(self, content):
        self.content = content

    def _get_base_report(self):
        """
        Reads header and footer
        """
        report = {}
        report["target_branch"] = re.search(r"Diff: (.*)\.\.\.", self.content).group(1)
        report["total"] = re.search(r"Total: (.*) line", self.content).group(1).strip()
        report["violations"] = re.search(r"Violations: (.*) line", self.content).group(1).strip()
        report["quality"] = re.search(r"Quality: (.*)", self.content).group(1).strip()
        return report

    def _process_content(self):
        pass

    def generate_report(self):
        if self.content and QUALITY_EMPTY_TEXT not in self.content:
            base_report = self._get_base_report()
            content_report = self._process_content()
            return {**base_report, **content_report}

        return False
