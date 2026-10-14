#!/usr/bin/env python3
"""Fetch the READMEs of the 30 most-starred public repos into corpus/ (issue #6).

The GitHub Search API ranks repositories by stars; each README is fetched
with the raw accept header and stored as corpus/<owner>---<repo>.md. The
manifest pins the query, the day, and one entry per repo, so the corpus
stays reproducible even though live search results drift.

Modes:
    python3 scripts/fetch_corpus.py           fetch and write corpus/ + manifest
    python3 scripts/fetch_corpus.py --check   verify committed corpus offline
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"

SEARCH_QUERY = "stars:>1 fork:false"
SORT = "stars"
ORDER = "desc"
PER_PAGE = 30
PINNED_FIELDS = ("full_name", "stars", "language", "readme_sha", "fetched_at")
RAW_ACCEPT = "application/vnd.github.raw"


class GuardError(RuntimeError):
    """Refusal raised before anything is written."""


def blob_sha(data: bytes) -> str:
    """Git blob SHA-1, the same value GitHub reports for the README blob."""
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def readme_path(corpus_dir: Path, full_name: str) -> Path:
    return corpus_dir / (full_name.replace("/", "---") + ".md")


def entry_from_item(item: dict) -> dict:
    """Keep only the fields the manifest pins for a search hit."""
    return {
        "full_name": item["full_name"],
        "stars": item["stargazers_count"],
        "language": item["language"],
    }


def gh_api(path: str, accept: str | None = None) -> bytes:
    cmd = ["gh", "api", path]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"gh api {path} failed ({result.returncode}): "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def search_repos() -> list[dict]:
    query = quote(SEARCH_QUERY, safe="")
    path = (
        f"search/repositories?q={query}"
        f"&sort={SORT}&order={ORDER}&per_page={PER_PAGE}"
    )
    data = json.loads(gh_api(path))
    return data["items"]


def fetch_readme(full_name: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            return gh_api(f"repos/{full_name}/readme", accept=RAW_ACCEPT)
        except RuntimeError as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"fetch_readme({full_name}) failed: {last_error}")


def fetch(
    corpus_dir: Path = CORPUS_DIR,
    manifest_path: Path = MANIFEST_PATH,
    force: bool = False,
) -> dict:
    """Fetch search results and READMEs, write the corpus and the manifest."""
    if manifest_path.exists() and not force:
        raise GuardError(
            f"{manifest_path} already exists and pins this corpus as evidence; "
            "re-run with --force to overwrite it"
        )
    today = datetime.now(timezone.utc).date().isoformat()
    corpus_dir.mkdir(parents=True, exist_ok=True)
    items = search_repos()
    if len(items) != PER_PAGE:
        raise RuntimeError(f"search returned {len(items)} repos, expected {PER_PAGE}")

    entries = []
    for item in items:
        entry = entry_from_item(item)
        data = fetch_readme(entry["full_name"])
        readme_path(corpus_dir, entry["full_name"]).write_bytes(data)
        entry["readme_sha"] = blob_sha(data)
        entry["fetched_at"] = today
        entries.append(entry)
        print(f"fetched {entry['full_name']} ({entry['stars']} stars)")

    manifest = {
        "query": SEARCH_QUERY,
        "sort": SORT,
        "order": ORDER,
        "per_page": PER_PAGE,
        "fetched_at": today,
        "repos": entries,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def check(corpus_dir: Path, manifest_path: Path) -> list[str]:
    """Verify a committed corpus against its manifest. Offline, no network."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read manifest {manifest_path}: {error}"]

    repos = manifest.get("repos")
    if not isinstance(repos, list):
        return ["manifest has no 'repos' list"]

    errors = []
    if len(repos) != PER_PAGE:
        errors.append(f"manifest lists {len(repos)} repos, expected {PER_PAGE}")

    seen = set()
    expected_files = set()
    for repo in repos:
        name = repo.get("full_name", "<missing full_name>")
        missing = [field for field in PINNED_FIELDS if field not in repo]
        if missing:
            errors.append(f"{name}: missing pinned field(s) {', '.join(missing)}")
        if name in seen:
            errors.append(f"{name}: duplicate entry")
        seen.add(name)
        if not isinstance(name, str) or "/" not in name:
            continue

        path = readme_path(corpus_dir, name)
        expected_files.add(path.name)
        if not path.is_file():
            errors.append(f"{path.name}: README file missing")
            continue
        if "readme_sha" in repo:
            actual = blob_sha(path.read_bytes())
            if actual != repo["readme_sha"]:
                errors.append(
                    f"{name}: readme_sha mismatch "
                    f"(manifest {repo['readme_sha']}, file {actual})"
                )

    for md in sorted(corpus_dir.glob("*.md")):
        if md.name not in expected_files:
            errors.append(f"{md.name}: stray file not covered by manifest")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed corpus against the manifest (offline)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing corpus and manifest",
    )
    args = parser.parse_args(argv)

    if args.check:
        errors = check(CORPUS_DIR, MANIFEST_PATH)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"{'FAIL' if errors else 'OK'}: "
            f"corpus {CORPUS_DIR} vs manifest {MANIFEST_PATH}"
        )
        return 1 if errors else 0

    try:
        manifest = fetch(force=args.force)
    except GuardError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        print(
            "A failed run may leave a partial corpus; re-running fetch "
            "(with --force if a manifest exists) overwrites it cleanly.",
            file=sys.stderr,
        )
        return 1
    print(f"wrote {len(manifest['repos'])} READMEs and {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
