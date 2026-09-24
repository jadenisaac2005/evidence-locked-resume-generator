# Résumé best practice for intern/new-grad ML candidates (research, Sept 2026)

**Scope and method.** About 15 sources, gathered in about 30 minutes of web search. **Caveat:** the network proxy
for this session blocked full-page fetches of most sources (harvard.edu, cmu.edu,
naceweb.org, theladders.com, techinterviewhandbook.org, venturebeat.com). Claims below
come from search-engine summaries of those pages. Where a number could not be checked
against the primary page, the rule says so.

**Evidence ratings**
- **A**: peer-reviewed or large-sample study
- **B**: guidance from a recruiter, a company or a university career centre
- **C**: vendor blog, résumé-builder site or commercial study with unpublished method

**Scope** is either *U* (universal) or *IN* (India-specific).

---

## 1. ATS parsing

| # | Rule (one line) | Source(s) | Evidence | Scope |
|---|---|---|---|---|
| 1.1 | Use one column, read top to bottom. Two-column layouts make some parsers (Taleo, iCIMS) interleave the sidebar with the main text. | [Resumemate two-column test](https://www.resumemate.io/blog/two-column-resumes-ats-tests-workarounds-and-examples/), [CVCraft 8-ATS test](https://cvcraft.roynex.com/blog/can-ats-read-tables-columns-formatting-2026), [ResumeOptimizerPro parser internals](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work) | C (consistent across vendors) | U |
| 1.2 | Don't put content in tables, text boxes, headers or footers. Contact details in a page header or footer are often dropped. | same as 1.1, [Interview Guys ATS guide](https://blog.theinterviewguys.com/what-ats-looks-for-in-resumes/) | C | U |
| 1.3 | Use standard section headings (Education, Projects, Skills, Experience). Parsers segment the text by matching heading names. | [ResumeOptimizerPro](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work), [Interview Guys](https://blog.theinterviewguys.com/what-ats-looks-for-in-resumes/) | C | U |
| 1.4 | The PDF must be text-based, made by a typesetter, not scanned or image-based. Image or "design-tool" PDFs are the most common cause of a near-zero parse. | [Interview Guys](https://blog.theinterviewguys.com/what-ats-looks-for-in-resumes/), [Resumly PDF errors](https://www.resumly.ai/blog/best-practices-for-pdf-resumes-to-avoid-ats-errors) | C | U |
| 1.5 | Ligatures (fi, fl) must map back to plain letters through the PDF's ToUnicode table. Otherwise words like "classifier" come out broken. Check the extracted text. | [ResumeXrays fonts](https://www.resumexrays.com/blog/the-fonts-ats-struggles-to-parse-and-why-it-costs-you), [dev.to ATS-view tool](https://dev.to/nilamadhab47/i-built-a-tool-that-shows-you-exactly-what-an-ats-reads-from-your-resume-heres-how-it-works-3c98) | C (the mechanism is standard PDF behaviour) | U |
| 1.6 | Use a common sans or serif font, 10–12 pt body text, and margins of about 0.5–1 in. | [Harvard OCS guide](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/) (10–12 pt), [ATS Resume AI spec](https://www.atsresumeai.com/blog/ats-resume-formatting-guide) | B | U |
| 1.7 | No icons, skill bars or rating graphics. They extract as junk or as nothing. | [Resumemate tables](https://www.resumemate.io/blog/are-tables-ats-friendly-why-they-break-parsing--5-safe-layouts/), [Google "How we hire"](https://www.google.com/about/careers/applications/how-we-hire/) (keep the format simple and consistent) | B/C | U |
| 1.8 | Write links as visible text (e.g. `github.com/…`), not as a hyperlink hidden behind a word. A parser, or a printout, only keeps the visible text. | follows from 1.4 and 1.5 | reasoning | U |

**Conflict: PDF or DOCX?** Several vendor tests say .docx parses slightly better
([Interview Guys](https://blog.theinterviewguys.com/what-ats-looks-for-in-resumes/)).
Greenhouse and Lever run native PDF text extraction
([ResumeOptimizerPro](https://resumeoptimizerpro.com/blog/how-resume-parsers-actually-work)),
and PDF keeps the layout fixed.
**Default: a text-based PDF, verified by a text-extraction check on every build.** A
DOCX export is out of scope. If a posting asks for .docx, paste the text dump
(`out/resume.txt`) into a word processor.

**Myth check: "75% of résumés are auto-rejected by ATS."** This traces to a 2012 sales
pitch by Preptel, a vendor that went out of business, and it never had a published method
([JobCannon trace](https://jobcannon.io/research/stats/ats-myth-preptel),
[Interview Guys](https://blog.theinterviewguys.com/ats-resume-rejection-myth/)).
Rejections mostly come from knockout questions such as work authorisation or location.
Parse quality still matters, because a garbled parse becomes a poor recruiter-facing
profile and makes keyword search miss you. **Rating: C, and the figure should be discounted.**

## 2. How recruiters scan

| # | Rule | Source(s) | Evidence | Scope |
|---|---|---|---|---|
| 2.1 | The first pass is a fast skim: name, education, titles and projects, dates, keywords. A simple layout with clear headings holds attention better. | [Ladders eye-tracking 2018](https://www.theladders.com/static/images/basicSite/pdfs/TheLadders-EyeTracking-StudyC2.pdf), [HR Dive](https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/541582/) | C (see note) | U |
| 2.2 | Spelling errors measurably reduce the chance of being shortlisted. Proofread, and keep text generated from checked data. | [Martin-Lacroux 2017, IJSA, n = 1,031 recruiters](https://onlinelibrary.wiley.com/doi/abs/10.1111/ijsa.12179), [PLOS One 2023](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0283280) | **A** | U |
| 2.3 | Employers screening students look first for evidence of problem-solving (about 90%) and technical skills (70% or more). | [NACE Job Outlook 2025](https://www.naceweb.org/research/reports/job-outlook/2025) | B (a large employer survey, but self-reported) | U (US sample) |

**About the "6–7 seconds" figure.** It comes from TheLadders, a commercial job site, in
2012 (6 s) and 2018 (7.4 s). The study is not peer-reviewed and is a small-sample
eye-tracking exercise. I could not reach the primary PDF to confirm the sample size.
Treat "the first pass is short, so put the strongest signal at the top" as the lesson.
Don't treat the exact seconds as a fact. **Rating: C.**

## 3. Bullet writing

| # | Rule | Source(s) | Evidence | Scope |
|---|---|---|---|---|
| 3.1 | Start each bullet with a strong action verb. Use past tense for finished work and present tense only for ongoing work. No "responsible for". | [Harvard OCS](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/), [CMU SCS guide](https://www.cmu.edu/career/documents/resources-by-college/scs/scs-resume-guide-2022.pdf) | B | U |
| 3.2 | No first person ("I", "my", "we"). | Harvard OCS, CMU (standard career-centre style) | B | U |
| 3.3 | Structure bullets as "Accomplished X, as measured by Y, by doing Z" (Laszlo Bock, Google). The result goes with a metric. | [Teal XYZ summary](https://www.tealhq.com/post/xyz-resume), [Laszlo Bock](https://en.wikipedia.org/wiki/Laszlo_Bock) | B (from a named Google executive, seen through secondary sources) | U |
| 3.4 | Keep each bullet to 2 rendered lines or fewer. Use 2–4 bullets per project and keep only what shows a skill or result. | [Tech Interview Handbook](https://www.techinterviewhandbook.org/resume/), Harvard OCS | B | U |
| 3.5 | Avoid buzzwords and filler ("passionate", "hardworking", "synergy", "leveraged", "cutting-edge"). Prefer concrete nouns and numbers. | Harvard OCS, [Google "How we hire"](https://www.google.com/about/careers/applications/how-we-hire/) | B | U |

## 4. Length, section order, what to cut

| # | Rule | Source(s) | Evidence | Scope |
|---|---|---|---|---|
| 4.1 | Students should fit on **one page**. Google sets no hard limit but says "think twice" before going past one page. Indian fresher guidance treats one page as effectively mandatory. | [Google "How we hire"](https://www.google.com/about/careers/applications/how-we-hire/), Harvard OCS, [IIT Madras internship résumé guidelines 2025-26](https://internship.iitm.ac.in/downloads/Internship_Resume_Guidelines_2025-26.pdf) | B | U + IN |
| 4.2 | Without work experience, a Projects section is the core of the résumé. List a few selected projects. | [Tech Interview Handbook](https://www.techinterviewhandbook.org/resume/), [Google "How we hire"](https://www.google.com/about/careers/applications/how-we-hire/) (recent grads should include projects) | B | U |
| 4.3 | Don't create empty sections, such as "Experience" with nothing in it. | follows from 4.2 and the "only what shows a skill" rule | reasoning | U |

**Conflict: Education or Projects first?** Career centres (CMU, Harvard) and most Indian
guidance put Education first for current students. Some tech-focused advice puts
Projects first when they are the strongest signal. **Default: Education first, kept to 2
lines**, so the Projects section still starts in the top third of the page. It matches
what Indian and international readers expect, and it keeps the graduation date that
screeners filter on. The order is configurable in `config/*.yaml`.

**Conflict: objective or summary line?** Vendor sites disagree. Some cite an Indeed
figure that 68% of employers like objectives, but I found no method for it (C). Career
centres advise removing generic objectives (B).
**Default: no objective or summary.** It costs 2–3 lines on a one-page résumé, and every
claim in it would need backing in the facts file anyway. The option could be added later
as a facts-backed field.

## 5. India-specific norms

| # | Rule | Source(s) | Evidence | Scope |
|---|---|---|---|---|
| 5.1 | No photo, date of birth, father's name, address or "declaration" on tech or MNC résumés. Photos are only for some government applications. | [Rezumea India](https://rezumea.com/resume-format/india), [ResumeGuru fresher guide](https://www.resumeguru.ai/blog/the-fresher-resume-guide-india), [Resumemate India](https://www.resumemate.io/blog/india-resume-format-cv-template-job-guide/) | C (consistent across sources) | IN |
| 5.2 | Write CGPA on its scale, e.g. "CGPA: 7.83/10", and never round it. Many sources suggest showing it only above a threshold (7.0–7.5). | [IIT Madras guidelines](https://internship.iitm.ac.in/downloads/Internship_Resume_Guidelines_2025-26.pdf) (no rounding), [PlacementScore IIT-D](https://placementscore.online/college/iit-delhi-placement-resume), [Rezup](https://www.rezup.in/resume-format/fresher) | B (placement-cell rules) / C | IN |
| 5.3 | Indian placement cells verify every claim against documents and remove unsupported ones. Evidence-locking matches that norm. | [IIT Madras guidelines](https://internship.iitm.ac.in/downloads/Internship_Resume_Guidelines_2025-26.pdf) | B | IN |
| 5.4 | Put the phone number (with country code, +91) and email in the body. International readers need the country code. | [Rezumea India](https://rezumea.com/resume-format/india), rule 1.2 | C | IN/U |

## 6. ML-specific signals

| # | Rule | Source(s) | Evidence | Scope |
|---|---|---|---|---|
| 6.1 | Metrics mean nothing without context. State the dataset, the split or test set, and a baseline next to each number. | Chip Huyen, quoted in [VentureBeat](https://venturebeat.com/ai/4-ai-and-ml-job-hunting-tips-from-chip-huyen) | B (a practitioner and author) | U |
| 6.2 | Leakage (such as duplicates across train and test, or tuning on the test set) is widespread and inflates results. Showing that you found and fixed it signals competence. | [Kapoor & Narayanan 2023, *Patterns*](https://www.cell.com/patterns/fulltext/S2666-3899(23)00159-9) (294 affected papers across 17 fields) | **A** | U |
| 6.3 | Link the code (GitHub) and any live demo for every project, so the reviewer can check the claim. | [Chip Huyen / VentureBeat](https://venturebeat.com/ai/4-ai-and-ml-job-hunting-tips-from-chip-huyen), [Tech Interview Handbook](https://www.techinterviewhandbook.org/resume/) | B | U |
| 6.4 | List only skills the projects show. Skills listed without evidence are discounted, and interviewers probe them. | [Chip Huyen / VentureBeat](https://venturebeat.com/ai/4-ai-and-ml-job-hunting-tips-from-chip-huyen) (expertise over keywords) | B | U |
| 6.5 | Say "synthetic" when the data is synthetic. Overclaiming real-world validity is the kind of gap 6.2 describes. | Kapoor & Narayanan 2023 | A (by extension) | U |

---

## Rules this generator enforces

These drive Phase 2 and are mapped to checks in `resume/checks.py`.

1. **Evidence lock.** Every number in the rendered text must appear in `facts.yaml`, and banned or retired claims fail the build. (Hard rules 1–3; research 5.3 and 6.2.)
2. **One page.** The page count must equal `max_pages` (default 1). (4.1)
3. **Single column, no tables, icons, graphics, or page headers and footers.** Enforced by the template design, which uses plain text blocks only. (1.1, 1.2, 1.7)
4. **Standard headings.** Only Education, Projects, Skills, and Experience (the last only when facts contain experience). (1.3, 4.3)
5. **Extraction check.** The PDF text must contain every heading and bullet in reading order, with no ligature code points (U+FB00–FB06) and no replacement characters. (1.4, 1.5)
6. **Visible URLs.** Links render as plain visible text. (1.8, 6.3)
7. **Bullet lint.**
   - Each bullet starts with an action verb from an allow-list (past tense, or present tense if the project is flagged ongoing).
   - No first person.
   - No buzzwords (the list is in config).
   - At most 2 rendered lines.
   - No two bullets on the page open with the same verb.
   - At most `max_bullets_per_project` bullets per project (3 in the default).
   - A warning when a project has no quantified bullet. (3.1–3.5)
8. **CGPA as written.** CGPA prints as `x/10`, unrounded, and can be switched on or off. (5.2)
9. **No personal extras.** The template has no fields for photo, date of birth or declaration. (5.1)
10. **Private data.** The phone comes from gitignored `data/private.yaml`. `resume-public.pdf` is built without it and fails on any phone-like pattern. (5.4)
11. **Missing-info report.** Lists project dates, phone and other gaps that the checks could find. (4.x)
12. **Tailoring.** The `--jd` flag reorders and selects existing facts only. It never rewrites them.

## Decisions added in revision 2

- **Personal site: a single line, not a bullet and not header-only.** The site is
  already in the contact line as the website link. Making it header-only would leave
  Next.js, TypeScript, Tailwind CSS and Vercel listed under Skills with nothing on the
  page to back them (rule 6.4). Its bullet had no measurable result (rule 3.4, and the
  lint warning). A one-line entry (name and stack) keeps those skills backed for one
  line and no bullet.
- **Density: 12 bullets, 3 per ML project.** One page leaves room to spare (rule 4.1).
  2–4 bullets per project, keeping only what shows a skill or result (rule 3.4).
  A fast first pass means fewer, stronger bullets get read (rule 2.1).
- **Result first, then method** (rule 3.3, the XYZ structure). The bullet opens with the
  outcome or finding a skimming reader should take away.
- **One opening verb per page.** Evidence: reasoning only (no study found). Repeated
  openers ("Found and fixed" ×4 in v1) blur together on a skim, and varying the verb
  forces each bullet to say what was distinctive about it.
- **Revision 4: personal site removed from the default résumé** (owner's decision). The
  site URL stays in the contact line, and the entry remains in `config/full.yaml`.
  Trade-off: TypeScript, Next.js, Tailwind CSS and Vercel are still listed under Skills,
  and are backed in facts.yaml (the skills check passes), but no project *on the page*
  shows them any more (rule 6.4).
