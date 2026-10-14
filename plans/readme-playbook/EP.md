# Epic — README playbook from the 30 most-starred GitHub repos

Label: `epic`

Build an evidence-based playbook for writing READMEs: fetch the READMEs of the 30 most-starred public repositories on GitHub, measure what they share, and turn the findings into a reusable template any project can apply.

Evidence: GitHub Search API `stars:>1 fork:false sort=stars order=desc` run 2026-10-14 returned 30 repos from `codecrafters-io/build-your-own-x` (553164 stars) down to `tensorflow/tensorflow` (200963 stars); {{L1}} pins that list in `corpus/manifest.json:1` and the fetcher in `scripts/fetch_corpus.py` (`fetch_corpus`). The chain below is `plans/readme-playbook/deps.tsv:1`.

## Done when

- [ ] {{L1}} merged: `corpus/manifest.json` on `main` lists 30 repos — `python3 -c "import json; assert len(json.load(open('corpus/manifest.json'))['repos'])==30"` exits 0 — owner: implementer
- [ ] {{L2}} merged: `analysis/report.md` on `main` — `grep -c '30/30' analysis/report.md` prints 1 or more — owner: implementer
- [ ] {{L3}} merged: `TEMPLATE.md` + `PLAYBOOK.md` on `main` — `test -f TEMPLATE.md && test -f PLAYBOOK.md` exits 0 — owner: implementer

## ADR stub

Research-only epic — deliverables are one fetch script plus markdown docs, not a service or app. Chosen because the owner's goal is guidance ("best README for any project"), not a monitoring product; a star-tracking tool was offered and deferred.

## Out of scope

- Building a star-tracking tool (owner deferred; separate epic if wanted).
- Rewriting this repo's own README with the resulting playbook (deferred).
