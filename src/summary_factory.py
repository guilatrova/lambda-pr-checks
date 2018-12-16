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
#RESUME_PLACEHOLDER#
```

#FOOTER#
"""


def truncate_string(string, width):
    truncate_diff = width - len(string)
    if truncate_diff < 0:
        start = -truncate_diff + 3
        return "..." + string[start:]
    return string


def create_coverage_summary(report, footer):
    # Len is 41
    # Content
    content = []
    for file in report["files"]:
        name = truncate_string(file[0], 33).ljust(33)
        value = file[1].rjust(7).ljust(8)
        content.append(f"{name}{value}")

    # Resume
    covered = "+ Covered lines"
    covered_value = report["total"].rjust(25).ljust(26)

    missing = "- Missing lines"
    missing_value = report["missing"].rjust(25).ljust(26)

    coverage = "+ Coverage"
    coverage_value = report["coverage"].rjust(30).ljust(31)
    resume = f"{covered}{covered_value}\n{missing}{missing_value}\n{coverage}{coverage_value}"

    # Summary
    summary = COVERAGE_REPORT.replace("#TARGET_BRANCH#", report["target_branch"])
    summary = summary.replace("#FOOTER#", footer)
    summary = summary.replace("#CONTENT_PLACEHOLDER#", "\n".join(content))
    summary = summary.replace("#RESUME_PLACEHOLDER#", resume)

    return summary.strip()


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
