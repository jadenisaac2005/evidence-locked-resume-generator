"""Tests for the checks themselves: each hard rule must actually fail the build."""
import copy
from pathlib import Path

import pytest
import yaml

from resume.build import ROOT, run
from resume.checks import Report, check_pdf
from resume.model import Document

FACTS = yaml.safe_load((ROOT / "data/facts.yaml").read_text())
CONFIG = yaml.safe_load((ROOT / "config/default.yaml").read_text())


def hyphen_doc():
    return Document(name="Jane Doe", paper="a4", font_size=11.0, max_pages=1, contact=[], sections=[
        {"kind": "projects", "title": "Projects", "projects": [{
            "id": "p", "name": "P", "context": None, "stack": [], "date": None, "links": [],
            "bullets": [{"id": "p/b", "supports": [], "text": "Measured ROC-AUC on a held-out split"}],
        }]},
    ])


def build(tmp_path: Path, facts=None, config=None, private=None, public=False):
    f = tmp_path / "facts.yaml"
    f.write_text(yaml.safe_dump(facts or FACTS, allow_unicode=True))
    priv = None
    if private is not None:
        priv = tmp_path / "private.yaml"
        priv.write_text(yaml.safe_dump(private))
    return run(facts_path=f, private_path=priv, pdf_path=tmp_path / "r.pdf",
               config_override=config or CONFIG, public=public)


def bullet(facts, pid, bid):
    p = next(p for p in facts["projects"] if p["id"] == pid)
    return next(b for b in p["bullets"] if b["id"] == bid)


def errors(res, kind):
    return [e for e in res.report.errors if e.startswith(f"[{kind}]")]


def errors_for(rep, kind):
    return [e for e in rep.errors if e.startswith(f"[{kind}]")]


def test_default_build_passes(tmp_path):
    res = build(tmp_path)
    assert res.report.ok, res.report.errors
    assert res.pages == 1


def test_invented_number_fails(tmp_path):
    facts = copy.deepcopy(FACTS)
    b = bullet(facts, "cpp-wasm", "accuracy")
    b["text"] = b["text"].replace("97.43%", "99.12%")
    res = build(tmp_path, facts)
    assert not res.report.ok
    assert any("99.12" in e for e in errors(res, "numbers")), res.report.errors   # hard rule 2 (PDF)
    assert any("99.12" in e for e in errors(res, "provenance"))                   # per-bullet


def test_number_only_in_bullet_wording_is_not_evidence(tmp_path):
    """Bullet wordings live in facts.yaml but are not evidence; ids like 'f3' aren't either."""
    facts = copy.deepcopy(FACTS)
    b = bullet(facts, "rockfall", "fixes")
    b["text"] += " in 999 days"
    res = build(tmp_path, facts)
    assert any("'999'" in e for e in errors(res, "numbers")), res.report.errors


@pytest.mark.parametrize("text", [
    "Reached 97.87% test accuracy",
    "Trained on a 72,000-article corpus",
    "Classified fake news headlines",
    "Built a model predicting rockfall incidents",
])
def test_banned_string_fails(tmp_path, text):
    facts = copy.deepcopy(FACTS)
    b = bullet(facts, "fake-news", "ablation")
    b["text"] = text
    res = build(tmp_path, facts)
    assert errors(res, "banned"), res.report.errors


def test_leaky_accuracy_only_as_comparison(tmp_path):
    facts = copy.deepcopy(FACTS)
    b = bullet(facts, "fake-news", "model")
    b["text"] = "Trained a TF-IDF model reaching 95.76% test accuracy"
    b["supports"] = ["f3"]
    res = build(tmp_path, facts)
    assert any("leaky" in e for e in errors(res, "banned")), res.report.errors


def test_rockfall_real_data_claim_fails(tmp_path):
    facts = copy.deepcopy(FACTS)
    bullet(facts, "rockfall", "fixes")["text"] = "Found and fixed issues seen on real-world mine data"
    res = build(tmp_path, facts)
    assert errors(res, "banned")


def test_rockfall_must_say_synthetic(tmp_path):
    cfg = copy.deepcopy(CONFIG)
    for p in cfg["projects"]:
        if p["id"] == "rockfall":
            p["bullets"] = ["serve", "fixes"]  # drops the only bullet that says "synthetic"
    res = build(tmp_path, config=cfg)
    assert errors(res, "caveat")


def test_two_pages_fails(tmp_path):
    cfg = copy.deepcopy(CONFIG)
    cfg["font_size"] = 16
    res = build(tmp_path, config=cfg)
    assert res.pages >= 2
    assert errors(res, "pages")


def test_lint_catches_weak_bullets(tmp_path):
    facts = copy.deepcopy(FACTS)
    bullet(facts, "fake-news", "ablation")["text"] = "Responsible for my passionate label fixes"
    res = build(tmp_path, facts)
    lint = " ".join(errors(res, "lint"))
    assert "action verb" in lint and "first person" in lint and "buzzword" in lint


def test_unevidenced_skill_fails(tmp_path):
    facts = copy.deepcopy(FACTS)
    facts["skills"][1]["items"].append("PyTorch")
    res = build(tmp_path, facts)
    assert any("PyTorch" in e for e in errors(res, "skills"))


def test_tailoring_only_reorders(tmp_path):
    from resume import tailor
    from resume.model import select
    jd = "ML intern: PyTorch, Docker, scikit-learn, NLP, TF-IDF, logistic regression, data leakage."
    cfg, ranking, gaps, kw = tailor.plan(copy.deepcopy(FACTS), CONFIG, jd)
    assert ranking[0]["id"] == "fake-news"
    assert "pytorch" in gaps and "docker" in gaps
    from resume.model import ascii_safe
    doc = select(copy.deepcopy(FACTS), cfg)
    all_bullets = {ascii_safe(b["text"]) for p in FACTS["projects"] for b in p["bullets"]}
    assert {b["text"] for b in doc.bullets()} <= all_bullets


def test_default_is_dense_enough(tmp_path):
    res = build(tmp_path)
    assert 11 <= len(res.doc.bullets()) <= 14


def test_repeated_opening_verb_fails(tmp_path):
    facts = copy.deepcopy(FACTS)
    bullet(facts, "rockfall", "fixes")["text"] = "Showed attention to threshold tuning on the test set"
    res = build(tmp_path, facts)
    assert any("open with 'showed'" in e for e in errors(res, "lint")), res.report.errors


def test_too_many_bullets_per_project_fails(tmp_path):
    cfg = copy.deepcopy(CONFIG)
    cfg["projects"][0]["bullets"] = ["accuracy", "weights", "loader", "demo"]
    res = build(tmp_path, config=cfg)
    assert any("max_bullets_per_project" in e for e in errors(res, "lint"))


def test_full_config_passes(tmp_path):
    full = yaml.safe_load((ROOT / "config/full.yaml").read_text())
    res = build(tmp_path, config=full)
    assert res.report.ok, res.report.errors
    assert len(res.doc.bullets()) == 16


def test_private_build_has_phone_public_does_not(tmp_path):
    res = build(tmp_path, private={"phone": "+91 00000 00000"})
    assert "00000 00000" in res.text and res.report.ok
    pub = build(tmp_path, public=True)
    assert "00000 00000" not in pub.text and pub.report.ok


def test_phone_in_public_pdf_fails(tmp_path):
    """E.g. someone puts the phone into facts.yaml instead of private.yaml."""
    facts = copy.deepcopy(FACTS)
    facts["identity"]["phone"] = "+91 00000 00000"
    res = build(tmp_path, facts, public=True)
    assert errors(res, "public"), res.report.errors


def test_ascii_output(tmp_path):
    from resume.model import ascii_safe
    assert ascii_safe("C++ Neural Network → WebAssembly") == "C++ Neural Network to WebAssembly"
    assert ascii_safe("(72,134 → 63,557 articles)") == "(72,134 to 63,557 articles)"
    assert ascii_safe("a 784 → 128 → 10 network") == "a 784-128-10 network"
    assert ascii_safe("784 → 128 (ReLU) → 10") == "784-128-10 (ReLU)"
    res = build(tmp_path)
    assert "→" not in res.text and "to WebAssembly" in res.text
    assert not [w for w in res.report.warnings if w.startswith("[ascii]")], res.report.warnings


def test_non_ascii_warns(tmp_path):
    facts = copy.deepcopy(FACTS)
    b = bullet(facts, "rockfall", "fixes")
    b["text"] = b["text"] + " ✓"
    res = build(tmp_path, facts)
    assert any(w.startswith("[ascii]") and "U+2713" in w for w in res.report.warnings)
    assert res.report.ok  # a warning, not a failure


def test_context_said_once(tmp_path):
    res = build(tmp_path)
    assert res.text.count("Smart India Hackathon 2025") == 1


def test_rockfall_eval_wording_is_not_a_real_data_claim(tmp_path):
    res = build(tmp_path)
    assert "served cutoff" in " ".join(res.text.split())
    assert not errors(res, "banned")


def test_hyphenated_token_split_across_a_line_break_fails(tmp_path):
    doc = hyphen_doc()
    rep = Report()
    check_pdf(doc, {"identity": {}}, "Measured ROC-\nAUC on a held-out split", pages=1, rep=rep)
    assert any("'ROC-AUC'" in e and "line break" in e for e in errors_for(rep, "ats")), rep.errors


def test_hyphenated_token_intact_on_one_line_passes(tmp_path):
    doc = hyphen_doc()
    rep = Report()
    check_pdf(doc, {"identity": {}}, "Measured ROC-AUC on a held-out split", pages=1, rep=rep)
    assert not any("line break" in e for e in errors_for(rep, "ats"))
