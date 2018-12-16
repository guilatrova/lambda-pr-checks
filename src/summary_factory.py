import os

STANDARD_SUMMARY = """
Some patterns errors were found:

```diff
Commits
=============
#PLACEHOLDER#
```

Read the [docs](#DOCS#) for more details
"""

COVERAGE_REPORT = """
## Coverage Report

> Comparing to #TARGET_BRANCH#

```diff
@@            Coverage Diff            @@
=========================================
+ Files                         Coverage
=========================================
#CONTENT_PLACEHOLDER#
=========================================
#RESUME_PLACEHOLDER#              100.0%
```

#FOOTER#
"""


def create_coverage_summary(report):
    # Len is 41
    summary = COVERAGE_REPORT.replace("#TARGET_BRANCH#", report["target_branch"])

    # Content
    content = []
    for file in report["files"]:
        name = file[0]
        value = file[1]
        content.append(f"{name}{value}")

    # Resume
    covered = "+ Covered lines"
    covered_value = report["total"].ljust(25).rjust(26)

    missing = "- Missing lines"
    missing_value = report["missing"].ljust(25).rjust(26)

    coverage = "+ Coverage"
    coverage_value = report["coverage"].ljust(30).rjust(31)
    resume = f"{covered}{covered_value}\n{missing}{missing_value}\n{coverage}{coverage_value}"


def create_standard_summary(commits):
    content = []
    for commit in commits:
        standard = "+" if commit["standard"] else "-"
        sha = commit["sha"][:7]
        message = commit["message"]
        content.append(f"{standard} {sha} {message}")

    joined = "\n".join(content)

    summary = STANDARD_SUMMARY.replace("#PLACEHOLDER#", joined)
    summary = summary.replace("#DOCS#", os.environ.get("DOCS_STANDARD_LINK", ""))

    return summary.strip()
