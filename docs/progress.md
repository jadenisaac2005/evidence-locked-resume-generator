# Progress

## Phase 1: Research (done)
1. Wrote docs/research.md: 6 topic tables and about 30 one-line rules. Each rule has source links, an evidence rating (A/B/C) and a scope (universal or India).
2. Only 2 findings are rated A (peer-reviewed): spelling errors hurt shortlisting (Martin-Lacroux 2017, n=1,031), and ML leakage is widespread (Kapoor & Narayanan 2023). The rest is recruiter or university guidance (B) or vendor claims (C).
3. Myth checks: the "6–7 s" figure is from the commercial Ladders study (C). The "75% ATS auto-reject" figure traces to a 2012 Preptel sales pitch (discount it).
4. Conflicts settled: text-based PDF over DOCX (verified by extraction), Education before Projects (kept to 2 lines), no objective or summary line.
5. Limitation: the proxy blocked most full-page fetches, so ratings rest on search summaries of the named primary sources. 12 enforceable rules feed Phase 2.

## Phase 2: Generator (done)
1. Built a Python package (`resume/`) with a Typst template. It has 3 runtime dependencies (typst, pypdf, PyYAML), and builds are byte-reproducible.
2. facts.yaml separates evidence (`facts`) from wordings (`bullets` that cite fact ids). Caveats became `guards` and `must_mention` checks.
3. Every build runs these checks: numbers vs evidence, per-bullet provenance, retired claims, caveats, page count, ATS extraction (headings on their own lines, reading order, ligatures), links, skill evidence, bullet lint (verb, first person, buzzwords, ≤2 rendered lines).
4. The checks caught 3 real bugs while I built it: URLs wrapping mid-address, headings merging with the next line in extraction, and fact ids (`f3`) counting as evidence for numbers.
5. `--jd` tailoring ranks and reorders existing bullets and reports gaps. There are 14 tests, covering invented numbers, banned strings, 2 pages, lint, unevidenced skills and tailoring. All pass.

## Phase 3: Résumé (done)
1. Built out/resume.pdf from config/default.yaml at 11 pt: 1 page, all checks pass, 1 warning (the portfolio bullet has no number).
2. The shareable copy, built without private.yaml, is in examples/ (resume.pdf, resume-ats-text.txt, missing-info.md).
3. Missing info: phone, dates for all 5 projects, coursework. Awards, certifications and experience are none recorded.
4. docs/critique.md covers strengths (evaluation context, leakage fixes, caveats enforced), weaknesses (no dates, dense page, no PyTorch), and 9 facts that would help most.
5. Next: add dates and a phone number, then rebuild. If space runs short, drop the portfolio or Rockfall service bullet via config.

## Revision 2 (done)
1. Facts: added the Rockfall 64.75% always-predict baseline and the GUARDED/ELEVATED precision/recall. NLP added to the fake-news stack and to Skills.
2. The default now has 12 result-first bullets (3 per ML project). The personal site is a single line (name and stack), which keeps the web skills backed without an unquantified bullet. The full 18-bullet set is in config/full.yaml.
3. New lint checks: one opening verb per page, and a max number of bullets per project. A template fix moves links to their own line when the header is full; the full config had surfaced "nlpgithub.com" in the extracted text.
4. Every build writes out/resume.pdf (private.yaml merged) and out/resume-public.pdf (never merged; the build fails on phone-like patterns or the real phone's digits).
5. 20 tests pass, and the default, full and tailored builds all pass every check.

## Revision 3 (done)
1. Added Rockfall facts: the base rate (64.75%, 12,950 of 20,000) and the three-level API. Bullets can now cite `context`, and the header then drops it (so "Smart India Hackathon 2024" appears once).
2. Rewrote the bullets: NumPy has 2, Rockfall has 3 (serve / cutoff trade-off / fixes), and the Fake News ablation stays within fact f5. The default now has 11 bullets, all ≤2 lines, with unique opening verbs.
3. X link turned off in config/default.yaml (still in facts.yaml and full.yaml).
4. `ascii_output`: arrows and other symbols become plain text in the PDF only. A new ascii check warns on non-ASCII characters other than – • ·. The default résumé has none.
5. Narrowed the Rockfall real-data ban to claims about real data, sites or events, so "real alert cutoff" is allowed. 24 tests pass.

## Revision 4 (done)
1. Extended fact f5: the top-weighted features are mostly source/format artifacts, confirmed against notebook cell 11 (reuters, image via, weekday names). The Fake News ablation bullet now uses that wording.
2. Duplicate counts reconciled and recorded in facts.yaml. 16,528 = all rows in the 7,951 duplicate groups; 8,577 = surplus copies removed (keep first). 16,528 − 7,951 = 8,577 = 72,134 − 63,557. The bullet now says "surplus copies".
3. Personal site removed from config/default.yaml; still in config/full.yaml.
4. Both PDFs are 1 page, all 11 bullets are ≤2 lines, and 24 tests pass.
