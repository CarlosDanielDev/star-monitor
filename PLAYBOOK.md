# README playbook

What the 30 most-starred repositories on GitHub do with their READMEs, and
what to copy. Every number below is measured over the pinned corpus in
`corpus/` and cites `analysis/report.md` (produced by
`scripts/analyze_corpus.py`; see #7 and #12). The fill-in skeleton that
implements these rules is [TEMPLATE.md](TEMPLATE.md).

## How to read the numbers

The report has two measures. The header-frequency table in
`analysis/report.md` counts exact normalized header text (lowercase, emoji
and punctuation stripped), so `install`, `installation`, and
`quick start` are three separate rows. The "Top patterns" list in
`analysis/report.md` counts broader properties (a README "with a
contributing header"), so its counts can be higher for the same concept.
When the two disagree, both are correct: they count different things.

## The rules

1. **Open with the project name.** 19/30 READMEs carry a top-level `#`
   title (`analysis/report.md`, Top patterns #1). It is the cheapest thing
   to get right and the first thing a rendered README shows.

2. **Front-load the artifact: title, badges, one-paragraph pitch.** Badges
   appear in 10/30 READMEs (`analysis/report.md`, Top patterns #2). The
   report measures presence, not position — putting them in the first
   screen is the epic's front-load call (ADR in #5/#8), not a measured
   finding.

3. **Show the thing.** 18/30 READMEs include at least one image or
   screenshot (`analysis/report.md`, Top patterns #4). A screenshot of the
   working artifact beats another paragraph of description.

4. **Put a working example before the theory.** 16/30 READMEs use fenced
   code blocks (`analysis/report.md`, Top patterns #5). One copy-pasteable
   snippet answers more questions than a feature list.

5. **Answer "how do I run it" in one section.** 12/30 READMEs have an
   install or quick-start section (`analysis/report.md`, Top patterns #6).
   The header table in `analysis/report.md` shows the concept split across
   three spellings — `install`, `installation`, `quick start` at 3/30
   each. Pick one canonical name ("Installation") so scanners find it.

6. **Invite contributions.** 18/30 READMEs have a contributing header
   (`analysis/report.md`, Top patterns #8). Say how to file bugs and send
   pull requests, or link the guide that does.

7. **Say where the community lives.** 15/30 READMEs have a community or
   support section (`analysis/report.md`, Top patterns #9). A chat, forum,
   or Discussions link tells readers the project responds.

8. **State the license, last.** 19/30 READMEs have a license section
   (`analysis/report.md`, Top patterns #7), and `license` is the single
   most common header in the corpus at 18/30 — 60% (header-frequency
   table in `analysis/report.md`). The report measures presence, not
   position; last is GitHub convention.

9. **Add a table of contents only when the document earns one.** 7/30
   READMEs have one (`analysis/report.md`, Top patterns #3). For scale:
   the median README is 163 non-blank lines outside code fences
   (`analysis/report.md`, Top patterns #10). Below roughly that median,
   navigation overhead is not worth a contents section.

10. **Calibrate length against the median, not the maximum.** Corpus
    READMEs span 29 to 2,522 non-blank lines outside code fences, median
    163 (`analysis/report.md`, Top patterns #10). The 2,522-line maximum
    is an outlier (a pure list repo), not a target.

11. **Say where the docs are and how to report a security issue.**
    `documentation` appears in 7/30 READMEs and `security` in 5/30
    (header-frequency table in `analysis/report.md`). Both rank below the
    top patterns, so the corpus does not argue for them on prevalence —
    the skeleton ships them because they answer questions every reader
    eventually asks, and this rule exists so every template section has a
    citation behind it.

## What to skip

- `sources and further reading` at 13/30 is the second-most-common header
  (header-frequency table in `analysis/report.md`), but the corpus is
  dominated by list and curation repositories — see `corpus/manifest.json`
  — where sources *are* the content. For a tool or library it is optional.
- Domain headers such as `books`, `machine learning`, and `c` (3/30 each,
  header-frequency table in `analysis/report.md`) are artifacts of which
  repos made the top 30, not patterns to copy.
- `miscellaneous` (5/30, header-frequency table in `analysis/report.md`)
  is a grab-bag header that tells the reader nothing. Fold its content
  into a named section.

## Anti-patterns

- **Splitting one concept across synonym headers.** `install`,
  `installation`, and `quick start` each poll at 3/30 instead of one
  9/30 row (header-frequency table in `analysis/report.md`). Readers —
  and any measurement — lose the count.
- **Writing past the corpus norm.** The longest README runs 2,522 lines
  while the median is 163 non-blank lines outside code fences
  (`analysis/report.md`, Top patterns #10). Length is a cost paid on every
  visit, not a virtue.
- **Omitting the license.** At 60% of the corpus, `license` is the most
  common header of all (header-frequency table in `analysis/report.md`);
  a README without one is the deviation, not the norm.
