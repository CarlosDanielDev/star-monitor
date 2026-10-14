"""Tests for scripts/fetch_corpus.py — corpus layout, blob shas, --check.

All tests run offline: no network, no gh subprocess. The fetch path itself is
a thin wrapper around `gh api`; the logic under test here is the pure code
(naming, sha computation, manifest validation).
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

import fetch_corpus  # noqa: E402


class BlobShaTest(unittest.TestCase):
    def test_matches_git_hash_object(self):
        # Expected values produced by `git hash-object --stdin`, which is the
        # same algorithm GitHub uses for blob SHAs.
        self.assertEqual(
            fetch_corpus.blob_sha(b"hello world\n"),
            "3b18e512dba79e4c8300dd08aeb37f8e728b8dad",
        )
        self.assertEqual(
            fetch_corpus.blob_sha(b"# T\n\nBody line.\n"),
            "94900fed9d2ee2ea7b0472beb271119704ca1f4b",
        )


class ReadmePathTest(unittest.TestCase):
    def test_slash_becomes_triple_dash(self):
        self.assertEqual(
            fetch_corpus.readme_path(Path("corpus"), "freeCodeCamp/freeCodeCamp"),
            Path("corpus") / "freeCodeCamp---freeCodeCamp.md",
        )


class EntryFromItemTest(unittest.TestCase):
    def test_keeps_only_pinned_fields(self):
        item = {
            "full_name": "owner/repo",
            "stargazers_count": 1234,
            "language": "Rust",
            "description": "noise",
            "fork": False,
        }
        self.assertEqual(
            fetch_corpus.entry_from_item(item),
            {"full_name": "owner/repo", "stars": 1234, "language": "Rust"},
        )

    def test_null_language_kept(self):
        item = {"full_name": "owner/repo", "stargazers_count": 1, "language": None}
        self.assertIsNone(fetch_corpus.entry_from_item(item)["language"])


class CheckTest(unittest.TestCase):
    """--check over a fabricated corpus in a tempdir (dobles, no network)."""

    N = 30

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        self.corpus.mkdir()
        self.repos = [
            {
                "full_name": f"owner{i}/repo{i}",
                "stars": 1000 - i,
                "language": "Python" if i % 2 else None,
                "readme_sha": fetch_corpus.blob_sha(b"readme %d\n" % i),
                "fetched_at": "2026-10-14",
            }
            for i in range(self.N)
        ]
        for i in range(self.N):
            (self.corpus / f"owner{i}---repo{i}.md").write_bytes(b"readme %d\n" % i)
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({"repos": self.repos}))

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self):
        return fetch_corpus.check(self.corpus, self.manifest)

    def test_consistent_corpus_has_no_errors(self):
        self.assertEqual(self.errors(), [])

    def test_sha_mismatch_reported(self):
        (self.corpus / "owner7---repo7.md").write_bytes(b"tampered\n")
        errs = self.errors()
        self.assertEqual(len(errs), 1)
        self.assertIn("owner7/repo7", errs[0])

    def test_missing_readme_reported(self):
        (self.corpus / "owner3---repo3.md").unlink()
        errs = self.errors()
        self.assertEqual(len(errs), 1)
        self.assertIn("owner3---repo3.md", errs[0])

    def test_missing_pinned_field_reported(self):
        manifest = json.loads(self.manifest.read_text())
        del manifest["repos"][11]["language"]
        self.manifest.write_text(json.dumps(manifest))
        errs = self.errors()
        self.assertEqual(len(errs), 1)
        self.assertIn("language", errs[0])

    def test_wrong_repo_count_reported(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["repos"] = manifest["repos"][: self.N - 1]
        self.manifest.write_text(json.dumps(manifest))
        errs = self.errors()
        count_errs = [e for e in errs if "expected 30" in e]
        self.assertEqual(count_errs, ["manifest lists 29 repos, expected 30"])

    def test_stray_md_reported(self):
        (self.corpus / "stray---extra.md").write_bytes(b"x\n")
        errs = self.errors()
        self.assertEqual(len(errs), 1)
        self.assertIn("stray---extra.md", errs[0])

    def test_duplicate_repo_reported(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["repos"][5] = manifest["repos"][4]
        self.manifest.write_text(json.dumps(manifest))
        dups = [e for e in self.errors() if "duplicate" in e]
        self.assertEqual(len(dups), 1)
        self.assertIn("owner4/repo4", dups[0])


class FetchGuardTest(unittest.TestCase):
    """fetch() must not silently overwrite a pinned manifest (gh mocked out)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        self.manifest = self.root / "corpus" / "manifest.json"
        items = [
            {"full_name": f"owner{i}/repo{i}", "stargazers_count": 900 - i, "language": None}
            for i in range(fetch_corpus.PER_PAGE)
        ]
        patcher = mock.patch.object(
            fetch_corpus, "search_repos", return_value=items
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        readme_patcher = mock.patch.object(
            fetch_corpus, "fetch_readme", return_value=b"stub readme\n"
        )
        readme_patcher.start()
        self.addCleanup(readme_patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def test_refuses_overwrite_without_force(self):
        self.corpus.mkdir()
        self.manifest.write_text('{"pinned": true}')
        with self.assertRaises(RuntimeError) as caught:
            with contextlib.redirect_stdout(io.StringIO()):
                fetch_corpus.fetch(self.corpus, self.manifest)
        self.assertIn("--force", str(caught.exception))
        self.assertEqual(self.manifest.read_text(), '{"pinned": true}')

    def test_force_overwrites(self):
        self.corpus.mkdir()
        self.manifest.write_text('{"pinned": true}')
        with contextlib.redirect_stdout(io.StringIO()):
            fetch_corpus.fetch(self.corpus, self.manifest, force=True)
        data = json.loads(self.manifest.read_text())
        self.assertEqual(len(data["repos"]), fetch_corpus.PER_PAGE)
        self.assertNotIn("pinned", data)


if __name__ == "__main__":
    unittest.main()
