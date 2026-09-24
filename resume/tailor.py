"""Tailoring: rank existing projects/bullets/skills against a job description.

Only SELECTS and REORDERS facts. No text is rewritten or added. Keyword extraction is
plain term matching (no LLM, no network).
"""
from __future__ import annotations

import copy
import re
from collections import Counter

from .checks import all_strings

STOP = set("""a about above across after again all also an and any are as at be because been
before being below between both but by can could did do does doing during each either etc
for from further had has have having how if in into is it its itself just may might more
most must no nor not of off on once only or other our out over own per same shall should
so some such than that the their them then there these they this those through to too
under until up upon very via was we were what when where which while who whom why will
with within without would you your yours
ability able apply candidate candidates company create day degree demonstrated desired
develop developing environment excellent experience familiarity good great help ideal
including internship intern interns job join knowledge looking months new opportunity plus
position preferred problem problems product products qualifications related requirements
responsibilities role skills strong students team teams understanding use using work
working world year years""".split())

# Technical vocabulary (lower-case). Facts vocabulary is added at runtime.
TECH = set("""pytorch tensorflow jax keras numpy pandas scikit-learn sklearn xgboost lightgbm
nltk spacy huggingface transformers llm llms nlp cv vision rag cuda triton onnx tensorrt
webassembly wasm emscripten python c++ c java javascript typescript go rust scala sql
nosql postgres mongodb redis spark hadoop airflow kafka docker kubernetes aws gcp azure
linux git ci/cd mlops mlflow fastapi flask django react next.js node.js tailwind vercel
backpropagation optimization optimizers adam sgd gradient deep learning machine statistics
probability linear algebra calculus classification regression clustering evaluation
metrics a/b experimentation deployment inference latency quantization distributed
training fine-tuning embeddings retrieval recommendation ranking tf-idf xgboost
logistic mnist benchmark benchmarks testing unit reproducibility research papers
math mathematics data pipelines api apis rest microservices""".split())

TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+#.-]*[A-Za-z0-9+#]|[A-Za-z]")


def tokens(text: str) -> list[str]:
    return [t.rstrip(".").lower() for t in TOKEN.findall(text)]


def keywords(jd: str, facts: dict) -> Counter:
    vocab = TECH | {t for s in all_strings(facts.get("projects")) + all_strings(facts.get("skills"))
                    for t in tokens(s) if t not in STOP and len(t) > 1}
    raw = TOKEN.findall(jd)
    toks = [t.rstrip(".").lower() for t in raw]
    kw = Counter()
    for orig, t in zip(raw, toks):
        if t in STOP:
            continue
        looks_tech = bool(re.search(r"[+#\d]|[a-z][A-Z]|^[A-Z]{2,}$", orig))
        if t in vocab or looks_tech:
            kw[t] += 1
    for a, b in zip(toks, toks[1:]):  # bigrams such as "machine learning"
        bg = f"{a} {b}"
        if a not in STOP and b not in STOP and bg in " ".join(all_strings(facts)).lower():
            kw[bg] += 1
    return kw


def _stem_pattern(term: str) -> str:
    """Crude stemming so 'classification' matches 'classifier' and 'testing' matches 'test'."""
    parts = []
    for w in term.split():
        s = re.sub(r"(ing|ed|es|s)$", "", w) if len(w) > 4 and w.isalpha() else w
        if len(s) >= 7 and s.isalpha():
            s = s[:6]
        parts.append(re.escape(s) + (r"[a-z]*" if s != w else ""))
    return r"\s+".join(parts)


def _has(term: str, text: str) -> bool:
    return re.search(rf"(?<![\w+#]){_stem_pattern(term)}(?![\w+#])", text.lower()) is not None


def score(text: str, kw: Counter) -> int:
    return sum(w for t, w in kw.items() if _has(t, text))


def plan(facts: dict, base_cfg: dict, jd: str, max_bullets: int = 3):
    """Return (config, ranking, gaps, keywords) for a tailored build."""
    kw = keywords(jd, facts)
    corpus = " ".join(all_strings({k: v for k, v in facts.items() if k != "_private"}))
    gaps = sorted((t for t in kw if not _has(t, corpus)), key=lambda t: -kw[t])

    default_order = [(s["id"] if isinstance(s, dict) else s) for s in base_cfg.get("projects", [])]
    # A project the base config shows as a single line (bullets: []) stays a single line.
    one_line = {s["id"] for s in base_cfg.get("projects", []) if isinstance(s, dict) and s.get("bullets") == []}
    ranking = []
    for p in facts.get("projects", []):
        head = " ".join([p["name"], p.get("context") or "", *p.get("stack", [])])
        bullets = []
        for i, b in enumerate(p.get("bullets", [])):
            pinned = any(w.lower() in b["text"].lower() for w in p.get("must_mention") or [])
            bullets.append({"id": b["id"], "score": score(b["text"], kw), "pinned": pinned, "i": i})
        bullets.sort(key=lambda b: (not b["pinned"], -b["score"], b["i"]))
        total = score(head, kw) + sum(b["score"] for b in bullets)
        prior = default_order.index(p["id"]) if p["id"] in default_order else len(default_order)
        ranking.append({"id": p["id"], "score": total, "prior": prior, "bullets": [] if p["id"] in one_line else bullets[:max_bullets]})
    ranking.sort(key=lambda r: (-r["score"], r["prior"]))

    cfg = copy.deepcopy(base_cfg)
    links = {(s["id"] if isinstance(s, dict) else s): (s.get("links", 1) if isinstance(s, dict) else 1)
             for s in base_cfg.get("projects", [])}
    cfg["projects"] = [{"id": r["id"], "links": links.get(r["id"], 1),
                        "bullets": [b["id"] for b in r["bullets"]]} for r in ranking]
    skills = [skill for g in facts.get("skills", []) for skill in all_strings(g["items"])]
    cfg["skills_priority"] = [s for s in skills if _has(s.lower(), " ".join(kw))]
    return cfg, ranking, gaps, kw


def drop_one(cfg: dict, ranking: list) -> str | None:
    """Remove the lowest-value item to make the page fit. Returns what was dropped."""
    scores = {r["id"]: {b["id"]: b for b in r["bullets"]} for r in ranking}
    proj_score = {r["id"]: r["score"] for r in ranking}
    zero = [p for p in cfg["projects"] if proj_score[p["id"]] == 0]
    if zero and len(cfg["projects"]) > 1:
        cfg["projects"].remove(zero[-1])
        return f"project {zero[-1]['id']} (no keyword overlap)"
    candidates = []
    for p in cfg["projects"]:
        for bid in p["bullets"]:
            b = scores[p["id"]][bid]
            if b["pinned"] or len(p["bullets"]) == 1:
                continue
            candidates.append((b["score"], proj_score[p["id"]], -b["i"], p["id"], bid))
    if candidates:
        *_, pid, bid = min(candidates)
        next(p for p in cfg["projects"] if p["id"] == pid)["bullets"].remove(bid)
        return f"bullet {pid}/{bid}"
    if len(cfg["projects"]) > 1:
        p = cfg["projects"].pop()
        return f"project {p['id']}"
    return None
