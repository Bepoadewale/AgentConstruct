#!/usr/bin/env python3
"""Validate AgentConstruct PR ticket and workload evidence conventions."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "docs" / "tickets"
TESTS = ROOT / "docs" / "test"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_ticket_files() -> None:
    if not TICKETS.is_dir():
        fail("docs/tickets/ is missing")

    readme = TICKETS / "README.md"
    if not readme.is_file():
        fail("docs/tickets/README.md is missing")

    ticket_files = sorted(TICKETS.glob("ticket*.md"))
    if not ticket_files:
        fail("docs/tickets/ must contain at least one ticketN.md file")

    for path in ticket_files:
        match = re.fullmatch(r"ticket([1-9][0-9]*)\.md", path.name)
        if not match:
            fail(f"ticket file must be named ticket<PR_NUMBER>.md: {path}")

        number = match.group(1)
        text = read(path)
        required = [
            f"# ticket{number}",
            "PR:",
            "Branch:",
            "## Problem / goal",
            "## Current repo state",
            "## Research / references used",
            "## Work planned for the PR",
            "## Acceptance criteria",
            "## Acceptance status",
            "## Tests / validation performed",
            "## Evidence files produced",
            "## Boundaries",
            "## Follow-up work",
        ]
        for marker in required:
            if marker not in text:
                fail(f"{path} is missing required marker: {marker}")

    github_pr_number = os.getenv("GITHUB_PR_NUMBER") or os.getenv("PR_NUMBER")
    github_event_name = os.getenv("GITHUB_EVENT_NAME")
    if github_event_name == "pull_request" and github_pr_number:
        expected = TICKETS / f"ticket{github_pr_number}.md"
        if not expected.is_file():
            fail(f"pull request #{github_pr_number} must include {expected.relative_to(ROOT)}")


def validate_customer_workload_tests() -> None:
    if not TESTS.is_dir():
        fail("docs/test/ is missing")

    readme = TESTS / "README.md"
    if not readme.is_file():
        fail("docs/test/README.md is missing")

    test_files = sorted(TESTS.glob("test*.md"))
    if not test_files:
        fail("docs/test/ must contain at least one test<PR_NUMBER>.md evidence file")

    numbers: list[int] = []
    for path in test_files:
        match = re.fullmatch(r"test([1-9][0-9]*)\.md", path.name)
        if not match:
            fail(f"test evidence file must be named test<PR_NUMBER>.md: {path}")
        number = match.group(1)
        numbers.append(int(number))

        matching_ticket = TICKETS / f"ticket{number}.md"
        if not matching_ticket.is_file():
            fail(f"{path.relative_to(ROOT)} must have matching {matching_ticket.relative_to(ROOT)}")

        text = read(path)
        required = [
            f"# test{number}",
            "Date:",
            "Execution type:",
            "Customer repository:",
            "Commit:",
            "AWS account:",
            "AWS region:",
            "## Resources created",
            "## Commands executed",
            "## Observed result",
            "## Teardown",
            "## Final boundary",
        ]
        for marker in required:
            if marker not in text:
                fail(f"{path} is missing required marker: {marker}")

    if len(numbers) != len(set(numbers)):
        fail(f"duplicate docs/test evidence numbers found: {numbers}")


def main() -> None:
    validate_ticket_files()
    validate_customer_workload_tests()
    print("Documentation convention checks passed.")


if __name__ == "__main__":
    main()
