# Critique of examples/resume.pdf against docs/research.md

## What's strong
- **Results come with their evaluation context** (rule 6.1). Every accuracy figure names the dataset and the test set, and gives a split, seed or baseline where the facts have one. That's rare for intern résumés and it backs up the positioning.
- **Evaluation-bug fixes show up in all four ML projects** (rule 6.2): the untrained-network loader, the leaky duplicate split plus the inverted labels, the EMA-form momentum, and tuning on the test set. This is the strongest differentiator, because leakage is a documented, widespread failure in ML work (Kapoor & Narayanan 2023, evidence A).
- **Caveats are kept, and the checks enforce them.** 97.33% is described as test digits, Rockfall says "synthetic", and 95.76% only appears as the leaky-split comparison.
- **The format meets every ATS rule in the research.** It is one page, single column, with standard headings, visible URLs and clean text extraction (no ligature or encoding problems). CGPA is written as 7.83/10. There is no photo, date of birth or objective.
- **Every listed skill is backed by a project**, so interviewers can probe any of them (rule 6.4).

## What's weak
1. **No dates anywhere.** Readers can't judge recency or progression, and the right-hand column of each project header is empty. This is the largest single gap.
2. **No phone number.** Indian recruiters expect one with +91 (rule 5.4).
3. **The page is dense.** It has 18 bullets, 13 of them two lines long. A fast skim (rule 2.1) will catch the headers and the first few words of each bullet. Several bullets open with the method rather than the result (rule 3.3): "Trained TF-IDF … : 95.22%" puts the number at the end.
4. **"Found and fixed" opens 4 bullets.** It's accurate, but repetitive. Varying the verb ("Caught", "Traced", "Corrected") is a wording change, not a new claim.
5. **No deep-learning framework.** The sample ML-intern JD reports PyTorch, NLP, deep learning, Docker, SQL and AWS as unsupported. PyTorch is the largest gap for applied-ML roles. The from-scratch work is a strong signal, but many screens filter on the framework keyword.
6. **The Rockfall numbers are modest** (ROC-AUC 0.75, 17.4% recall) and the data is synthetic. It is presented honestly, which fits the brand, but it's the weakest ML project. For research-engineer roles, consider cutting its service bullet first.
7. **The portfolio bullet has no measurable result.** It's the first candidate to drop if space is needed, for example after dates and a phone number are added.
8. **The x.com link** is low-value for recruiters and costs space on the contact line. It can be toggled off in `config/default.yaml`.

## Facts that would most improve it (suggestions, not claims)
1. **Month/year for each project** (`dates:` in facts.yaml).
2. **Phone number** (in data/private.yaml).
3. **Multi-seed optimizer results for the NumPy project** (mean ± std over N seeds). This would turn "too close to rank" into a claim you can defend.
4. **In-browser inference latency for the WebAssembly demo** (ms per prediction on a named device). It's a cheap measurement and relevant to systems work.
5. **A cross-dataset test for the fake-news model** (train on WELFake, test on another corpus). It would put a number on the "relies on outlet style" finding.
6. **A simple baseline for Rockfall** (for example, logistic regression on the same split), so 0.75 ROC-AUC has a reference point.
7. **Relevant coursework**, only if real: linear algebra, probability, ML, DSA.
8. **A small project in PyTorch.** Only once it exists, and ideally in the same evaluate-honestly style.
9. **An "NLP" / "text classification" label for the fake-news project in facts.yaml.** It's true, and it would close a common keyword gap without changing any number.

---

## Revision 2: before and after

| | v1 | v2 |
|---|---|---|
| Bullets | 18 (13 of them two lines) | 12 (3 per ML project), plus a one-line site entry |
| Bullet openings | method first; "Found and fixed" ×4 | result or finding first; 12 different verbs (enforced by lint) |
| Rockfall evaluation | ROC-AUC 0.75 with no reference point | against the 64.75% always-predict-rockfall baseline |
| NLP keyword | a gap in tailoring | in the fake-news stack and skills |
| Outputs | one PDF | `resume.pdf` (private) + `resume-public.pdf` (fails on phone patterns) |

**Still open:** project dates and a phone number (see missing-info.md). The "fixed"
evaluation-bug bullets for fake news (inverted labels) and the Rockfall threshold
trade-off are available in `config/full.yaml` but not in the default.
