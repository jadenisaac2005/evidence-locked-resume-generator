"""CLI: python -m resume build [--config ...] [--jd job.txt] [--no-private]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import tailor
from .build import ROOT, run, write_outputs
from .model import BuildError, load_facts, load_yaml


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="resume")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="render out/resume.pdf and run all checks")
    b.add_argument("--facts", default=ROOT / "data/facts.yaml", type=Path)
    b.add_argument("--private", default=ROOT / "data/private.yaml", type=Path)
    b.add_argument("--no-private", action="store_true", help="only build the public PDF (no private.yaml)")
    b.add_argument("--config", default=ROOT / "config/default.yaml", type=Path)
    b.add_argument("--lint", default=ROOT / "config/lint.yaml", type=Path)
    b.add_argument("--out", default=ROOT / "out", type=Path)
    b.add_argument("--jd", type=Path, help="job description text file: tailor selection/order")
    a = ap.parse_args(argv)

    private = None if a.no_private else a.private
    try:
        if a.jd:
            return _tailored(a, private)
        rc = 0
        if not a.no_private:  # for direct applications: private.yaml merged
            res = run(a.facts, a.config, private, a.lint, a.out / ".build/resume.pdf")
            rc |= _finish(res, a.out, "resume")
        # for the website: never merges private.yaml; fails on anything phone-like
        pub = run(a.facts, a.config, None, a.lint, a.out / ".build/resume-public.pdf", public=True)
        rc |= _finish(pub, a.out, "resume-public", missing=a.no_private)
        return rc
    except BuildError as e:
        print(f"BUILD FAILED: {e}", file=sys.stderr)
        return 1


def _finish(res, out: Path, stem: str, missing: bool = True) -> int:
    final = write_outputs(res, out, stem, missing)
    for w in res.report.warnings:
        print(f"warning {w}")
    if missing:
        print(f"missing info: {len(res.missing)} item(s) -> {out / 'missing-info.md'}")
    if not res.report.ok:
        print(f"\nBUILD FAILED ({len(res.report.errors)} error(s)); PDF kept as {final}", file=sys.stderr)
        for e in res.report.errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print(f"OK: {final} ({res.pages} page), text dump {out / (stem + '.txt')}")
    return 0


def _tailored(a, private) -> int:
    facts = load_facts(a.facts, private)
    base = load_yaml(a.config)
    jd = a.jd.read_text(encoding="utf-8")
    cfg, ranking, gaps, kw = tailor.plan(facts, base, jd, base.get("max_bullets_per_project", 3))
    dropped = []
    for _ in range(40):
        res = run(a.facts, None, private, a.lint, a.out / ".build/resume-tailored.pdf", config_override=cfg)
        if res.pages <= res.doc.max_pages:
            break
        what = tailor.drop_one(cfg, ranking)
        if what is None:
            break
        dropped.append(what)

    lines = ["# Tailoring report", "", f"JD: {a.jd}", "",
             "## JD keywords (weight = mentions)", ""]
    lines += [f"- {t} ×{w}" + ("" if t not in gaps else "  **(no support in facts)**") for t, w in kw.most_common()]
    lines += ["", "## Suggested order (score = keyword overlap)", ""]
    kept = {p["id"]: p["bullets"] for p in cfg["projects"]}
    for r in ranking:
        mark = "" if r["id"] in kept else "  (not included)"
        lines.append(f"{r['id']}: {r['score']}{mark}")
        for bl in r["bullets"]:
            inc = "✓" if bl["id"] in kept.get(r["id"], []) else "·"
            lines.append(f"    {inc} {bl['id']}: {bl['score']}" + ("  (pinned: caveat)" if bl["pinned"] else ""))
    lines += ["", "## Dropped to fit the page", ""] + [f"- {d}" for d in dropped or ["nothing"]]
    lines += ["", "## Gaps: JD keywords with no support in facts.yaml", ""] + [f"- {g}" for g in gaps or ["none"]]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "tailor-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[lines.index("## Suggested order (score = keyword overlap)"):]))
    return _finish(res, a.out, "resume-tailored")


if __name__ == "__main__":
    sys.exit(main())
