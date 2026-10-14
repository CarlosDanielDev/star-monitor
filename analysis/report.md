# README pattern report

What the 30 most-starred READMEs share, measured over the pinned
corpus in `corpus/` (fetched 2026-10-14). Analysis reads
only committed files — no network — and
`python3 scripts/analyze_corpus.py --check` re-derives this report
byte for byte.

## Coverage

Coverage: 30/30 READMEs listed in `corpus/manifest.json`.

## Header frequency

Top 20 headers across
the corpus, as a count out of the READMEs analyzed. A header is an
ATX line of level 1-3, lowercased with emoji and punctuation
stripped (`## 🚀 Getting Started` and `## Getting started` are one
pattern); lines inside fenced code blocks are skipped.

| Header | Count | Share |
| --- | ---: | ---: |
| license | 18/30 | 60% |
| source s and further reading | 13/30 | 43% |
| contributing | 11/30 | 37% |
| documentation | 7/30 | 23% |
| miscellaneous | 5/30 | 17% |
| security | 5/30 | 17% |
| table of contents | 5/30 | 17% |
| community | 4/30 | 13% |
| resources | 4/30 | 13% |
| books | 3/30 | 10% |
| c | 3/30 | 10% |
| development | 3/30 | 10% |
| install | 3/30 | 10% |
| installation | 3/30 | 10% |
| machine learning | 3/30 | 10% |
| quick start | 3/30 | 10% |
| agents | 2/30 | 7% |
| business | 2/30 | 7% |
| contents | 2/30 | 7% |
| contribution | 2/30 | 7% |

## Top patterns

### 1. Top-level title

Present in 19/30 READMEs with a `#` title line.
examples: public-apis/public-apis, EbookFoundation/free-programming-books

### 2. Badge images

Present in 10/30 READMEs with at least one badge image.
examples: freeCodeCamp/freeCodeCamp, EbookFoundation/free-programming-books

### 3. Table of contents

Present in 7/30 READMEs with a table-of-contents header.
examples: sindresorhus/awesome, freeCodeCamp/freeCodeCamp

### 4. Screenshots or images

Present in 18/30 READMEs with at least one image.
examples: codecrafters-io/build-your-own-x, public-apis/public-apis

### 5. Fenced code blocks

Present in 16/30 READMEs with at least one fenced code block.
examples: openclaw/openclaw, donnemartin/system-design-primer

### 6. Install or quick-start section

Present in 12/30 READMEs with an install/quick-start header.
examples: openclaw/openclaw, obra/superpowers

### 7. License section

Present in 19/30 READMEs with a license header.
examples: codecrafters-io/build-your-own-x, public-apis/public-apis

### 8. Contributing section

Present in 18/30 READMEs with a contributing header.
examples: codecrafters-io/build-your-own-x, freeCodeCamp/freeCodeCamp

### 9. Community or support section

Present in 15/30 READMEs with a community/support header.
examples: openclaw/openclaw, donnemartin/system-design-primer

### 10. Document length

Median 163 non-blank lines per README; longest is public-apis/public-apis (2522), shortest is deepseek-ai/deepseek-harness (29).
examples: deepseek-ai/deepseek-harness, public-apis/public-apis
