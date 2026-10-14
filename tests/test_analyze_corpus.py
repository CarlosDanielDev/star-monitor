"""Tests for scripts/analyze_corpus.py — headers, patterns, report, --check.

All tests run offline over a fabricated corpus in a tempdir (dobles, no
network); the committed corpus is never touched.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import analyze_corpus  # noqa: E402


def readme_a():
    return "\n".join(
        [
            "# Project A",
            "",
            "![badge](https://img.shields.io/badge/a-b.svg)",
            "",
            "## Table of Contents",
            "",
            "- [Install](#install)",
            "",
            "## Installation",
            "",
            "```bash",
            "# this comment is not a header",
            "pip install a",
            "```",
            "",
            "## License",
            "",
            "MIT. See CONTRIBUTING.",
            "",
            "![screenshot](docs/a.png)",
            "",
            "## Contributing",
            "",
            "PRs welcome.",
            "",
            "## Appendix",
            "",
            "Long-form filler so this fixture is the longest document:",
            "one", "two", "three", "four", "five",
            "six", "seven", "eight", "nine", "ten",
        ]
    )


def readme_b():
    return "\n".join(
        [
            "# Project B",
            "",
            "![badge](https://img.shields.io/badge/b-b.svg)",
            "",
            "## Contents",
            "",
            "- [Usage](#usage)",
            "",
            "## Quick Start",
            "",
            "~~~python",
            "print('hi')",
            "~~~",
            "",
            "![screenshot](docs/b.png)",
            "",
            "## Contributing",
            "",
            "PRs welcome.",
            "",
            "## Community",
            "",
            "Ask in the chat.",
        ]
    ) + "\n"


def readme_c():
    return "\n".join(
        [
            "## License",
            "",
            "Apache-2.0.",
            "",
            "## Support",
            "",
            "Open an issue.",
        ]
    ) + "\n"


class CorpusTestCase(unittest.TestCase):
    """Three fabricated repos chosen so every measured pattern has >= 2 hits."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        self.corpus.mkdir()
        self.names = ["ownerA/repoA", "ownerB/repoB", "ownerC/repoC"]
        bodies = [readme_a(), readme_b(), readme_c()]
        for name, body in zip(self.names, bodies):
            (self.corpus / (name.replace("/", "---") + ".md")).write_text(
                body, encoding="utf-8"
            )
        self.manifest = self.corpus / "manifest.json"
        self.manifest.write_text(
            json.dumps({"fetched_at": "2026-10-14", "repos": [
                {"full_name": name} for name in self.names
            ]}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def analysis(self):
        return analyze_corpus.analyze_corpus(self.corpus, self.manifest)


class NormalizeHeaderTest(unittest.TestCase):
    def test_lowercases_and_strips_emoji_and_punctuation(self):
        self.assertEqual(
            analyze_corpus.normalize_header("\U0001F680 Getting Started!"),
            "getting started",
        )
        self.assertEqual(analyze_corpus.normalize_header("C++"), "c")

    def test_keeps_unicode_words(self):
        self.assertEqual(analyze_corpus.normalize_header("常见问题"), "常见问题")

    def test_collapses_whitespace(self):
        self.assertEqual(
            analyze_corpus.normalize_header("  Build   your  own  "), "build your own"
        )


class SplitHeadersTest(unittest.TestCase):
    def test_counts_levels_one_to_three(self):
        text = "# a\n\n## b\n\n### c\n\n#### d\n"
        self.assertEqual(analyze_corpus.split_headers(text), ["a", "b", "c"])

    def test_skips_fenced_code_lines(self):
        text = "## real\n\n```bash\n# not a header\npip i x\n```\n\n~~~python\n# also not\n~~~\n"
        self.assertEqual(analyze_corpus.split_headers(text), ["real"])

    def test_unclosed_fence_drops_the_rest(self):
        text = "## real\n\n```bash\n## swallowed\n"
        self.assertEqual(analyze_corpus.split_headers(text), ["real"])


class RepoMetricsTest(unittest.TestCase):
    def test_blank_lines_do_not_count_toward_length(self):
        self.assertEqual(analyze_corpus.repo_metrics("# t\n\n\nbody\n")["lines"], 2)


class AnalyzeCorpusTest(CorpusTestCase):
    def test_header_frequency_counts_across_repos(self):
        freq = self.analysis()["header_freq"]
        self.assertEqual(freq["license"], 2)
        # readme_c hits the community pattern via "support"; freq keeps the
        # literal normalized header text.
        self.assertEqual(freq["community"], 1)
        self.assertEqual(freq["support"], 1)
        self.assertEqual(freq["project a"], 1)  # H1 titles count too; low rank keeps them out of the table

    def test_total_is_corpus_size(self):
        self.assertEqual(self.analysis()["total"], 3)

    def test_pattern_counts_match_corpus(self):
        counts = {p["label"]: p["count"] for p in self.analysis()["patterns"]}
        self.assertEqual(counts["Top-level title"], 2)
        self.assertEqual(counts["Badge images"], 2)
        self.assertEqual(counts["Table of contents"], 2)
        self.assertEqual(counts["Screenshots or images"], 2)
        self.assertEqual(counts["Fenced code blocks"], 2)
        self.assertEqual(counts["Install or quick-start section"], 2)
        self.assertEqual(counts["License section"], 2)
        self.assertEqual(counts["Contributing section"], 2)
        self.assertEqual(counts["Community or support section"], 2)

    def test_examples_are_two_or_more_repos_in_manifest_order(self):
        for pattern in self.analysis()["patterns"]:
            self.assertGreaterEqual(len(pattern["examples"]), 2, pattern["label"])
        toc = next(p for p in self.analysis()["patterns"] if p["label"] == "Table of contents")
        self.assertEqual(toc["examples"], ["ownerA/repoA", "ownerB/repoB"])

    def test_length_pattern_carries_median_and_extremes(self):
        length = next(p for p in self.analysis()["patterns"] if p["label"] == "Document length")
        self.assertEqual(length["examples"], ["ownerC/repoC", "ownerA/repoA"])
        self.assertIn("Median", length["summary"])

    def test_deterministic_across_runs(self):
        self.assertEqual(self.analysis(), self.analysis())


class RenderReportTest(CorpusTestCase):
    def render(self):
        return analyze_corpus.render_report(self.analysis())

    def test_header_table_has_a_row_per_listed_header_plus_frame(self):
        table_lines = [ln for ln in self.render().splitlines() if ln.startswith("|")]
        listed = self.analysis()["header_freq"]
        expected_rows = min(analyze_corpus.TABLE_ROWS, len(listed))
        self.assertEqual(len(table_lines), expected_rows + 2)

    def test_coverage_line_states_total_out_of_total(self):
        self.assertIn("3/3", self.render())

    def test_every_pattern_has_an_examples_line_with_two_repos(self):
        lines = self.render().splitlines()
        examples = [ln for ln in lines if ln.startswith("examples:")]
        self.assertEqual(len(examples), len(self.analysis()["patterns"]))
        for line in examples:
            named = [tok for tok in line[len("examples:"):].split(",") if tok.strip()]
            self.assertGreaterEqual(len(named), 2, line)

    def test_no_trailing_whitespace_anywhere(self):
        for line in self.render().splitlines():
            self.assertEqual(line, line.rstrip(), repr(line))


class CheckTest(CorpusTestCase):
    def report_path(self):
        path = self.root / "analysis" / "report.md"
        path.parent.mkdir()
        return path

    def test_matching_report_has_no_errors(self):
        path = self.report_path()
        path.write_text(analyze_corpus.render_report(self.analysis()), encoding="utf-8")
        self.assertEqual(analyze_corpus.check(path, self.corpus, self.manifest), [])

    def test_tampered_report_reported(self):
        path = self.report_path()
        path.write_text(analyze_corpus.render_report(self.analysis()), encoding="utf-8")
        path.write_text(
            path.read_text(encoding="utf-8").replace("3/3", "2/3", 1), encoding="utf-8"
        )
        errors = analyze_corpus.check(path, self.corpus, self.manifest)
        self.assertEqual(len(errors), 1)
        self.assertIn(str(path), errors[0])
        # --check is read-only: the committed report must come back untouched.
        self.assertIn("2/3", path.read_text(encoding="utf-8"))

    def test_missing_report_reported(self):
        errors = analyze_corpus.check(self.report_path(), self.corpus, self.manifest)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing", errors[0])


class MainCliTest(CorpusTestCase):
    """main() turns unreadable corpus input into a clean error, not a traceback."""

    def setUp(self):
        super().setUp()
        for name, target in (
            ("CORPUS_DIR", self.corpus),
            ("MANIFEST_PATH", self.manifest),
            ("REPORT_PATH", self.root / "analysis" / "report.md"),
        ):
            patcher = mock.patch.object(analyze_corpus, name, target)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = analyze_corpus.main(argv)
        return code, err.getvalue()

    def test_check_with_broken_manifest_reports_error(self):
        self.manifest.write_text("{not json", encoding="utf-8")
        code, err = self.run_main(["--check"])
        self.assertEqual(code, 1)
        self.assertIn("ERROR:", err)
        self.assertNotIn("Traceback", err)

    def test_default_mode_with_broken_manifest_reports_error(self):
        self.manifest.write_text("{not json", encoding="utf-8")
        out = self.root / "analysis"
        code, err = self.run_main([])
        self.assertEqual(code, 1)
        self.assertIn("ERROR:", err)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
