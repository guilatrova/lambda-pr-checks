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
