#!/usr/bin/env python3
"""Write analysis/report.md measuring what the 30 pinned READMEs share (issue #7).

Reads only the committed corpus (corpus/*.md + corpus/manifest.json) — no
network — so every number in the report is reproducible offline. Headers are
ATX lines of level 1-3, lowercased with emoji and punctuation stripped, so
`## 🚀 Getting Started` and `## Getting started` count as one pattern; lines
inside fenced code blocks never count (a shell comment is not a header).

Modes:
    python3 scripts/analyze_corpus.py           write analysis/report.md
    python3 scripts/analyze_corpus.py --check   verify the committed report
"""

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"
REPORT_PATH = ROOT / "analysis" / "report.md"

TABLE_ROWS = 20

FENCE = re.compile(r"^(```|~~~)")
ATX = re.compile(r"^(#{1,3}) (.+)$")
H1 = re.compile(r"^# ")
NON_WORD = re.compile(r"[^\w\s]|_")
SPACES = re.compile(r"\s+")
COMMUNITY = re.compile(r"community|support|sponsor|acknowledg|discuss|faq")
INSTALL = ("install", "quick start", "quickstart", "getting started", "usage", "setup")
TOC = ("table of contents", "contents", "toc")


def normalize_header(text: str) -> str:
    """Lowercase and strip emoji/punctuation so variants count as one pattern."""
    return SPACES.sub(" ", NON_WORD.sub(" ", text.lower())).strip()


def split_headers(text: str) -> list[str]:
    """Normalized text of every level 1-3 ATX header outside fenced blocks."""
    headers = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if FENCE.match(stripped):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = ATX.match(stripped)
        if match:
            headers.append(normalize_header(match.group(2)))
    return headers


def repo_metrics(text: str) -> dict:
    """Per-README measurements: headers plus the binary pattern markers."""
    metrics = {
        "headers": [],
        "h1": False,
        "fences": 0,
        "images": 0,
        "badges": 0,
        "lines": 0,
    }
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if FENCE.match(stripped):
            in_fence = not in_fence
            metrics["fences"] += 1
            continue
        if in_fence:
            continue
        if stripped:
            metrics["lines"] += 1
        match = ATX.match(stripped)
        if match:
            header = normalize_header(match.group(2))
            metrics["headers"].append(header)
            if H1.match(stripped):
                metrics["h1"] = True
        if "![" in stripped:
            metrics["images"] += 1
            if "shields.io" in stripped or "badge" in stripped.lower():
                metrics["badges"] += 1
    return metrics


def has_header(headers: list[str], predicate) -> bool:
    return any(predicate(header) for header in headers)


def pattern_defs() -> list[tuple[str, str, object]]:
    """(label, summary-format subject, hit test) for every measured pattern.

    The hit test receives a repo's metrics dict; binary patterns return a
    bool, the document-length pattern returns its line count as the value.
    """
    return [
        ("Top-level title", "a `#` title line",
         lambda m: m["h1"]),
        ("Badge images", "at least one badge image",
         lambda m: m["badges"] > 0),
        ("Table of contents", "a table-of-contents header",
         lambda m: has_header(m["headers"], lambda h: h in TOC)),
        ("Screenshots or images", "at least one image",
         lambda m: m["images"] > 0),
        ("Fenced code blocks", "at least one fenced code block",
         lambda m: m["fences"] > 0),
        ("Install or quick-start section", "an install/quick-start header",
         lambda m: has_header(
             m["headers"], lambda h: h.startswith(INSTALL))),
        ("License section", "a license header",
         lambda m: has_header(m["headers"], lambda h: "license" in h)),
        ("Contributing section", "a contributing header",
         lambda m: has_header(m["headers"], lambda h: "contribut" in h)),
        ("Community or support section", "a community/support header",
         lambda m: has_header(m["headers"], lambda h: COMMUNITY.search(h))),
        ("Document length", "non-blank lines",
         lambda m: m["lines"]),
    ]


def analyze_corpus(
    corpus_dir: Path = CORPUS_DIR, manifest_path: Path = MANIFEST_PATH
) -> dict:
    """Measure the pinned corpus; pure, deterministic, offline."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repos = manifest["repos"]
    total = len(repos)

    header_freq: Counter = Counter()
    measured = []
    for repo in repos:
        name = repo["full_name"]
        path = corpus_dir / (name.replace("/", "---") + ".md")
        metrics = repo_metrics(path.read_text(encoding="utf-8", errors="replace"))
        header_freq.update(metrics["headers"])
        measured.append((name, metrics))

    patterns = []
    for label, subject, hit in pattern_defs():
        values = [(name, hit(metrics)) for name, metrics in measured]
        hits = [name for name, value in values if value]
        examples = hits[:2]
        if label == "Document length":
            lines = sorted(measured, key=lambda item: item[1]["lines"])
            shortest, longest = lines[0], lines[-1]
            median = statistics.median([m["lines"] for _, m in measured])
            summary = (
                f"Median {median:g} {subject} per README; longest is "
                f"{longest[0]} ({longest[1]['lines']:g}), shortest is "
                f"{shortest[0]} ({shortest[1]['lines']:g})."
            )
            examples = [shortest[0], longest[0]]
            count = len(hits)
        else:
            summary = f"Present in {len(hits)}/{total} READMEs with {subject}."
            count = len(hits)
        patterns.append(
            {"label": label, "summary": summary, "count": count, "examples": examples}
        )

    return {
        "total": total,
        "fetched_at": manifest.get("fetched_at", "unknown"),
        "header_freq": dict(header_freq),
        "patterns": patterns,
    }


def render_report(analysis: dict) -> str:
    """Render the analysis as the committed markdown report."""
    total = analysis["total"]
    lines = [
        "# README pattern report",
        "",
        f"What the {total} most-starred READMEs share, measured over the pinned",
        f"corpus in `corpus/` (fetched {analysis['fetched_at']}). Analysis reads",
        "only committed files — no network — and",
        "`python3 scripts/analyze_corpus.py --check` re-derives this report",
        "byte for byte.",
        "",
        "## Coverage",
        "",
        f"Coverage: {total}/{total} READMEs listed in `corpus/manifest.json`.",
        "",
        "## Header frequency",
        "",
        f"Top {min(TABLE_ROWS, len(analysis['header_freq']))} headers across",
        "the corpus, as a count out of the READMEs analyzed. A header is an",
        "ATX line of level 1-3, lowercased with emoji and punctuation",
        "stripped (`## 🚀 Getting Started` and `## Getting started` are one",
        "pattern); lines inside fenced code blocks are skipped.",
        "",
        "| Header | Count | Share |",
        "| --- | ---: | ---: |",
    ]
    ranked = sorted(
        analysis["header_freq"].items(), key=lambda item: (-item[1], item[0])
    )
    for header, count in ranked[:TABLE_ROWS]:
        lines.append(f"| {header} | {count}/{total} | {round(100 * count / total)}% |")
    lines += ["", "## Top patterns", ""]
    for index, pattern in enumerate(analysis["patterns"], start=1):
        lines += [
            f"### {index}. {pattern['label']}",
            "",
            pattern["summary"],
            f"examples: {', '.join(pattern['examples'])}",
            "",
        ]
    return "\n".join(lines).rstrip("\n") + "\n"


def check(
    report_path: Path, corpus_dir: Path, manifest_path: Path
) -> list[str]:
    """Verify the committed report still matches a fresh run. Offline."""
    if not report_path.is_file():
        return [f"{report_path}: missing report; run scripts/analyze_corpus.py"]
    expected = render_report(analyze_corpus(corpus_dir, manifest_path))
    actual = report_path.read_text(encoding="utf-8")
    if actual == expected:
        return []
    actual_lines = actual.splitlines()
    expected_lines = expected.splitlines()
    where = next(
        (
            str(n)
            for n, (a, e) in enumerate(
                zip(actual_lines, expected_lines), start=1
            )
            if a != e
        ),
        str(min(len(actual_lines), len(expected_lines)) + 1),
    )
    return [
        f"{report_path}: committed report does not match a fresh run "
        f"(first difference at line {where}); re-run scripts/analyze_corpus.py"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed report matches a fresh run (offline)",
    )
    args = parser.parse_args(argv)

    try:
        if args.check:
            errors = check(REPORT_PATH, CORPUS_DIR, MANIFEST_PATH)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"{'FAIL' if errors else 'OK'}: report {REPORT_PATH}")
            return 1 if errors else 0

        analysis = analyze_corpus(CORPUS_DIR, MANIFEST_PATH)
    except (OSError, json.JSONDecodeError, KeyError) as error:
        print(
            f"ERROR: cannot analyze the corpus under {CORPUS_DIR}: {error}",
            file=sys.stderr,
        )
        print(
            "Nothing was written. Validate the corpus with "
            "`python3 scripts/fetch_corpus.py --check` first.",
            file=sys.stderr,
        )
        return 1

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(analysis), encoding="utf-8")
    print(f"wrote {REPORT_PATH} from {analysis['total']} READMEs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
