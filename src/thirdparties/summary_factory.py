import os

STANDARD_SUMMARY = """
## Guidelines Report

```diff
@@         FineTune Guidelines        @@
========================================
+ Item    Message
========================================
#CONTENT_PLACEHOLDER#
========================================
#RESUME_PLACEHOLDER#
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

COV_REPORT_FOOTER = "See details in the [**coverage report**](#COV_LINK#)."

QUALITY_REPORT = """
## Quality Report

> Comparing to #TARGET_BRANCH#

```diff
@@            Quality  Diff            @@
=========================================
+ Files                          Quality
=========================================
#CONTENT_PLACEHOLDER#
=========================================
#RESUME_PLACEHOLDER#
```

#FOOTER#
"""

QUALITY_REPORT_FOOTER = "See details in the [**quality report**](#QUALITY_LINK#)."


def truncate_string(string, width):
    truncate_diff = width - len(string)
    if truncate_diff < 0:
        start = -truncate_diff + 3
        return "..." + string[start:]
    return string


def _create_summary_report(template, report, resume, footer):
    # Len is 41
    # Content
    content = []
    for file in report["files"]:
        name = truncate_string(file["file"], 33).ljust(33)
        value = file["value"].rjust(7).ljust(8)
        content.append(f"{name}{value}")

    summary = template.replace("#TARGET_BRANCH#", report["target_branch"])
    summary = summary.replace("#FOOTER#", footer)
    summary = summary.replace("#CONTENT_PLACEHOLDER#", "\n".join(content))
    summary = summary.replace("#RESUME_PLACEHOLDER#", resume)

    return summary.strip()


def create_coverage_summary(report, footer):
    if report:
        covered = "+ Covered lines"
        covered_value = report["total"].rjust(25).ljust(26)

        missing = "- Missing lines"
        missing_value = report["missing"].rjust(25).ljust(26)

        coverage = "+ Coverage"
        coverage_value = report["coverage"].rjust(30).ljust(31)
        resume = f"{covered}{covered_value}\n{missing}{missing_value}\n{coverage}{coverage_value}"

        return _create_summary_report(COVERAGE_REPORT, report, resume, footer)

    return ""


def create_coverage_footer(link):
    return COV_REPORT_FOOTER.replace("#COV_LINK#", link)


def create_quality_summary(report, footer):
    if report:
        total = "+ Total lines"
        total_value = report["total"].rjust(27).ljust(28)

        violation = "- Violation lines"
        violation_value = report["violations"].rjust(23).ljust(24)

        quality = "+ Quality"
        quality_value = report["quality"].rjust(31).ljust(32)
        resume = f"{total}{total_value}\n{violation}{violation_value}\n{quality}{quality_value}"

        return _create_summary_report(QUALITY_REPORT, report, resume, footer)

    return ""


def create_quality_footer(link):
    return QUALITY_REPORT_FOOTER.replace("#QUALITY_LINK#", link)


def create_standard_summary(report, resume):
    content = []

    def get_sign(standard):
        return "+" if standard else "-"

    # Title
    title_sign = get_sign(report["title"]["standard"])
    title_message = report["title"]["message"]
    first_line = f"{title_sign} TITLE   {title_message}"
    content.append(first_line)

    # Commits
    for commit in report["commits"]:
        sign = get_sign(commit["standard"])
        sha = commit["sha"][:7]
        message = commit["message"]
        content.append(f"{sign} {sha} {message}")

    joined = "\n".join(content)

    summary = STANDARD_SUMMARY.replace("#CONTENT_PLACEHOLDER#", joined)
    summary = summary.replace("#DOCS#", os.environ.get("DOCS_STANDARD_LINK", ""))
    summary = summary.replace("#RESUME_PLACEHOLDER#", resume)

    return summary.strip()
