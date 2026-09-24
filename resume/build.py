"""Build pipeline: load → select → pre-checks → render → PDF checks → outputs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import checks
from .model import BuildError, Document, load_facts, load_yaml, select
from .render import extract, render

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Result:
    doc: Document
    report: checks.Report
    pdf: Path
    text: str
    pages: int
    line_counts: dict
    missing: list


def run(facts_path=ROOT / "data/facts.yaml", config=ROOT / "config/default.yaml",
        private_path=ROOT / "data/private.yaml", lint_path=ROOT / "config/lint.yaml",
        pdf_path=ROOT / "out/.build/resume.pdf", config_override: dict | None = None,
        public: bool = False) -> Result:
    """Render and check. Never raises for check failures; see Result.report."""
    facts = load_facts(facts_path, private_path)
    cfg = config_override if config_override is not None else load_yaml(config)
    if not cfg:
        raise BuildError(f"config missing or empty: {config}")
    lint = load_yaml(lint_path)
    doc = select(facts, cfg)

    rep = checks.Report()
    checks.check_claims(facts, doc, rep)
    pdf_path = Path(pdf_path)
    line_counts = render(doc, pdf_path)
    text, pages = extract(pdf_path)
    checks.check_lint(doc, facts, lint, rep, line_counts)
    checks.check_pdf(doc, facts, text, pages, rep)
    if public:
        # Built without private.yaml, but the real phone (if any) is still loaded for the leak check.
        real = load_yaml(ROOT / "data/private.yaml") if private_path is None else {}
        checks.check_public(text, {**facts, "_private": real or facts.get("_private")}, rep)
    missing = checks.missing_info(facts, doc, rep)
    return Result(doc, rep, pdf_path, text, pages, line_counts, missing)


def write_outputs(res: Result, out_dir: Path, stem: str = "resume", missing: bool = True) -> Path:
    """Write the text dump, missing-info report and check log. On failure the PDF is
    renamed to <stem>.failed.pdf so a failing build never leaves a usable résumé behind."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{stem}.txt").write_text(res.text, encoding="utf-8")
    if missing:
        (out_dir / "missing-info.md").write_text(
            "# Missing info\n\nFields a strong résumé needs that facts.yaml / private.yaml lack.\n"
            "Fill them in; never guess.\n\n" + "".join(f"- {m}\n" for m in res.missing), encoding="utf-8")
    log = [f"pages: {res.pages}/{res.doc.max_pages}",
           f"bullet lines: {res.line_counts}", "", "ERRORS:"] + (res.report.errors or ["none"]) \
        + ["", "WARNINGS:"] + (res.report.warnings or ["none"])
    (out_dir / f"{stem}.checks.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    final = out_dir / f"{stem}.pdf"
    if res.report.ok:
        if res.pdf != final:
            res.pdf.replace(final)
        (out_dir / f"{stem}.failed.pdf").unlink(missing_ok=True)
    else:
        failed = out_dir / f"{stem}.failed.pdf"
        res.pdf.replace(failed)
        final.unlink(missing_ok=True)
        final = failed
    return final
