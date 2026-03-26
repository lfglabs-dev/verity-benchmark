#!/usr/bin/env python3
"""Check that the pinned verity dependency is not too far behind upstream main.

Reads the pinned SHA from lakefile.lean, queries GitHub for the distance
between that SHA and the upstream default branch, and warns or fails if
the pin is stale.

Usage:
    python3 scripts/check_verity_pin_staleness.py [--max-commits N] [--warn-only]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Match: require verity from git "...url..."@"<sha>"
_PIN_RE = re.compile(
    r'require\s+verity\s+from\s+git\s+"(?P<url>[^"]+)"@"(?P<sha>[0-9a-f]+)"'
)

DEFAULT_MAX_COMMITS = 100


def extract_pin(lakefile: Path) -> tuple[str, str]:
    """Return (repo_url, sha) from lakefile.lean."""
    text = lakefile.read_text(encoding="utf-8")
    m = _PIN_RE.search(text)
    if not m:
        print("ERROR: could not find verity git pin in lakefile.lean", file=sys.stderr)
        sys.exit(1)
    return m.group("url"), m.group("sha")


def github_nwo_from_url(url: str) -> str:
    """Extract 'owner/repo' from a GitHub URL."""
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    parts = url.split("/")
    return f"{parts[-2]}/{parts[-1]}"


def commits_behind(nwo: str, pinned_sha: str) -> int | None:
    """Return number of commits on main ahead of pinned_sha, or None on error."""
    result = subprocess.run(
        ["gh", "api", f"repos/{nwo}/compare/{pinned_sha}...HEAD", "--jq", ".ahead_by"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def pinned_commit_date(nwo: str, sha: str) -> str | None:
    """Return the ISO date of the pinned commit, or None on error."""
    result = subprocess.run(
        ["gh", "api", f"repos/{nwo}/commits/{sha}", "--jq", ".commit.committer.date"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Check verity pin staleness.")
    parser.add_argument(
        "--max-commits",
        type=int,
        default=DEFAULT_MAX_COMMITS,
        help=f"Fail if the pin is more than N commits behind (default: {DEFAULT_MAX_COMMITS})",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print a warning instead of failing",
    )
    args = parser.parse_args()

    lakefile = ROOT / "lakefile.lean"
    url, sha = extract_pin(lakefile)
    nwo = github_nwo_from_url(url)

    print(f"Verity pin: {sha[:12]} (from {nwo})")

    date = pinned_commit_date(nwo, sha)
    if date:
        print(f"Pin date:   {date}")

    behind = commits_behind(nwo, sha)
    if behind is None:
        print("WARNING: could not determine commit distance (gh API error)", file=sys.stderr)
        if not args.warn_only:
            sys.exit(1)
        return

    print(f"Commits behind main: {behind}")

    if behind > args.max_commits:
        msg = (
            f"Verity pin is {behind} commits behind main "
            f"(threshold: {args.max_commits}). "
            f"Consider bumping the pin in lakefile.lean."
        )
        if args.warn_only:
            print(f"WARNING: {msg}", file=sys.stderr)
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"OK: verity pin is {behind} commits behind main (within threshold of {args.max_commits})")


if __name__ == "__main__":
    main()
