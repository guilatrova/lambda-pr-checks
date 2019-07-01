import re


class CircleCommitDTO:
    """
    DTO that represents the commit processed by CircleCI
    in order to generate the report.
    """
    def __init__(
        self, owner, project, commit_sha, build_num,
        quality_tool, repo_id=None, pr_link=None
    ):
        # GitHub
        self.owner = owner
        self.project = project
        self.commit_sha = commit_sha

        # CircleCI
        self.build_num = build_num
        self.repo_id = repo_id
        self.pr_link = pr_link

    @staticmethod
    def create_from_dynamodb(report, repo_id):
        quality_tool = report.get("quality_tool", "flake8")

        return CircleCommitDTO(
            report["owner"],
            report["project"],
            report["commit_sha"],
            report["build_num"],
            quality_tool,
            repo_id=repo_id,
        )

    @staticmethod
    def create_from_circleci(cievent, quality_tool):
        pr_link = cievent.get("pr_link", False)

        return CircleCommitDTO(
            cievent["owner"],
            cievent["project"],
            cievent["commit_sha"],
            cievent["build_num"],
            quality_tool,
            pr_link=pr_link
        )

    def get_reports_links(self):
        """
        Returns artifacts links from CircleCI
        """
        reports = {
            "coverage": {
                "name": "coverage.html",
                "url": f"https://{self.build_num}-{self.repo_id}-gh.circle-artifacts.com/0/quality-reports/coverage.html",
            },
            "flake8": {
                "name": "flake8.html",
                "url": f"https://{self.build_num}-{self.repo_id}-gh.circle-artifacts.com/0/quality-reports/flake8.html",
            },
            "eslint": {
                "name": "eslint.html",
                "url": f"https://{self.build_num}-{self.repo_id}-gh.circle-artifacts.com/0/quality-reports/eslint.html",
            },
        }

        return reports

    def _extract_pr_data(self):
        """
        Extracts owner, repo and PR number from regular PR url.
        Expected format: https://github.com/:owner/:repo/pull/:number
        """
        matches = re.findall(r"github\.com\/(.*)\/(.*)\/pull\/(\d+)", self.pr_link)[0]
        return {"owner": matches[0], "project": matches[1], "pr_number": matches[2]}

    def get_pr_urls(self):
        """
        Returns a tuple with Summary URL and Status URL
        """
        data = self._extract_pr_data()
        pr_number = data["pr_number"]

        summary_url = (
            f"https://api.github.com/repos/{self.owner}/{self.project}/issues/{pr_number}/comments"
        )
        statuses_url = f"https://api.github.com/repos/{self.owner}/{self.project}/statuses/{self.commit_sha}"

        return (summary_url, statuses_url)
