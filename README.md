# Evidence-locked résumé generator

Built with Claude Code from my spec; the facts and constraints are mine.

This tool builds a one-page, ATS-safe PDF résumé from a single facts file. The build
**fails** if the résumé contains a number that isn't in the facts, a retired claim, or
a caveat violation. It also fails when the page overflows, when the PDF text doesn't
extract cleanly, or when a bullet breaks the lint rules. Output is byte-for-byte
reproducible.

The rules come from [docs/research.md](docs/research.md), which lists sources with evidence ratings.

## Quick start

```sh
make setup                      # pip install typst pypdf PyYAML pytest
cp data/private.example.yaml data/private.yaml   # add your phone (gitignored)
make resume                     # → out/resume.pdf (with private.yaml) + out/resume-public.pdf (without)
make tailor JD=job.txt          # → out/resume-tailored.pdf + out/tailor-report.md
make test
make full                       # → out/full/: the full 18-bullet set (config/full.yaml)
make sample                     # → examples/: copies of the public build (safe to commit)
```

The equivalent CLI command is `python -m resume build [--config config/x.yaml] [--jd job.txt] [--no-private]`.

Every build writes two PDFs:

| Output | private.yaml | Use |
|---|---|---|
| `out/resume.pdf` (+ `resume.txt`) | merged (phone) | direct applications |
| `out/resume-public.pdf` (+ `resume-public.txt`) | **never** merged | your website; the build fails if anything phone-like is in it |

`--no-private` builds only the public PDF.
Exit code 1 means the build failed. The PDF is then kept as `*.failed.pdf`, so a
failing build never leaves a usable `resume.pdf` behind.

## Files

| File | Role |
|---|---|
| `data/facts.yaml` | **The single source of truth.** Identity, education, projects, skills. |
| `data/private.yaml` | Gitignored. Phone number (and an optional email override), merged into `identity` at build time. The template is `data/private.example.yaml`. |
| `config/default.yaml` | **Selects and orders content only.** Sets which projects, which bullets and in what order, the section order, page limit, max bullets per project (3), paper size, font size and the CGPA toggle. It selects 12 bullets. |
| `config/full.yaml` | The full 18-bullet set with 2 links per project, for picking from or for a longer CV. |
| `config/lint.yaml` | Allowed action verbs, buzzword list, first-person patterns, max rendered lines per bullet. |
| `resume/template.typ` | Typst template. It adds no content: everything arrives as JSON. |
| `resume/checks.py` | All checks. The retired claims are hard-coded here on purpose, so a config edit can't switch them off. |

## Editing facts

Each project has three kinds of content:

- **`facts`**: verified statements with ids (`f1`, `f2`, …). This is the evidence.
- **`bullets`**: résumé wordings. Each bullet lists the facts it `supports`. Every number in a bullet must appear in those cited facts. A bullet may also cite `context` (the project's context line). The header then leaves the context out, so it isn't said twice.
- **`guards` / `must_mention`**: caveats turned into checks. For example, `97.33` must appear next to "test digits" or "MNIST", and the Rockfall text must say "synthetic".

To add a result, first add it as a fact. Then write a bullet that cites it, and select the bullet in `config/default.yaml`.
Unknown values stay `null` or `MISSING` and show up in the missing-info report. They never reach the PDF.

Skills must appear in some project's `stack`, or carry an explicit `evidence:` note (as Git does).

## Checks (run on every build)

| Check | Fails when | Research rule |
|---|---|---|
| **numbers** | A number in the extracted PDF text isn't in the facts. Bullet wordings, ids and guards don't count as evidence, so a number typed only into a bullet is caught. | Hard rule 2 |
| **provenance** | A bullet contains a number that its cited facts don't contain, or it cites no facts. | 5.3 |
| **banned** | Retired claims appear: 97.87%, "72,000-article", "fake news headlines", "predicting rockfall incidents". Also 95.76% without "leaky", or any real-world wording for the synthetic Rockfall data. | Hard rule 3, 6.2 |
| **caveat** | A project guard or a `must_mention` word is violated. | 6.5 |
| **pages** | The page count is greater than `max_pages` (default 1). | 4.1 |
| **ats** | pypdf text extraction finds a problem: a heading not on its own line, a heading or bullet missing or out of reading order, ligature code points (U+FB00–FB06), U+FFFD, private-use characters or control characters. | 1.1–1.5 |
| **links** | Visible URL text doesn't match a link in the facts. This also catches URLs split across lines. | 1.8 |
| **skills** | A listed skill has no project or explicit evidence. | 6.4 |
| **lint** | A bullet doesn't start with an allowed action verb (present tense is allowed only for `ongoing: true` projects), uses first person, contains a buzzword, or renders to more than 2 lines (measured inside Typst). Two bullets on the page open with the same verb. A project has more than `max_bullets_per_project` bullets. A project with no number only triggers a *warning*. | 3.1–3.5 |
| **ascii** (warning) | Extracted text contains any non-ASCII character other than `–`, `•` and `·`. With `ascii_output: true`, output text is made ASCII-safe at render time, and facts.yaml keeps the originals: `784 → 128 → 10` becomes `784-128-10`, any other `→` becomes "to", `28×28` becomes `28x28`, `≥` becomes `>=`, and `—` becomes `–`. | 1.5 |
| **public** | `resume-public.pdf` contains a phone-like pattern (10 or more digits, allowing `+`, spaces, dots, dashes and parentheses), or the digits of the phone in private.yaml. | Hard rule 4, 5.4 |
| **missing-info** | Never fails. It writes `out/missing-info.md`: phone, project dates, coursework, and the facts file's own `unknown_fill_in_later` list. | – |

## Tailoring (`--jd`)

The tailoring step extracts keywords from the job description. It uses no LLM and no
network: it matches against a small tech vocabulary plus the facts' own vocabulary, with
bigrams and light stemming. Then it:

1. Scores every project and bullet by keyword overlap. Projects are ordered by score; ties keep the default order.
2. Keeps the top `max_bullets_per_project` bullets per project, picked from *all* fact bullets, not just the default selection. A project the config shows as a single line stays a single line. Bullets that satisfy a caveat, such as Rockfall's "synthetic" bullet, are pinned.
3. Moves matched skills to the front of their group.
4. Renders the page. If it doesn't fit, it drops the lowest-value item and renders again, until the page fits.
5. Writes `out/tailor-report.md`: keywords, ranking, what was dropped, and **gaps** (JD keywords that nothing in facts.yaml supports).

Tailoring only selects and reorders. The same checks run on the tailored PDF, and
`tests/test_checks.py::test_tailoring_only_reorders` asserts that every tailored bullet is an existing fact bullet.

## Writing bullets

Lead with the result or finding, then the method. For example: "Cut epochs to 97% MNIST test accuracy from 26 (SGD) to 4 (Momentum)… with … written by hand in NumPy."
Every bullet across all projects opens with a different verb, so any selection passes the unique-verb lint.

## Why Typst (not LaTeX)

- **Install.** The whole compiler is one pip wheel (`typst`). A usable LaTeX needs a TeX distribution of several hundred MB, which is a heavy dependency for a small tool.
- **Speed and determinism.** A build takes well under a second. With `ignore_system_fonts` and `date: none`, the PDF is byte-identical on every machine. The body font is Libertinus Serif, which is bundled with Typst.
- **Measurable layout.** Typst's `measure` and `query` report each bullet's rendered line count back to Python, which is how the 2-line lint works without heuristics.
- **Clean text layer.** Typst writes ToUnicode maps, and ligatures are also turned off. The ATS check verifies the extracted text on every build rather than trusting this.
- **Single-column, text-only layout.** It has no tables, icons, graphics or page header/footer. URLs are visible text inside non-breaking boxes.
