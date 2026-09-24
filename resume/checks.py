"""Checks that run on every build. Errors fail the build; warnings are reported.

Maps to the "rules this generator enforces" list in docs/research.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .model import Document, display_url, skill_name

# --- Hard rule 3: retired claims. Kept in code (not config) so they can't be switched off.
RETIRED = [
    (r"97\.87", "retired accuracy 97.87%"),
    (r"72,?000[\s-]*article", "retired '72,000-article' claim"),
    (r"fake news headlines", "retired 'fake news headlines' framing"),
    (r"predicting rockfall incidents", "retired 'predicting rockfall incidents' claim"),
]
# 95.76% may only appear as the leaky-split comparison.
CONTEXT_ONLY = [(r"95\.76", r"leaky", "95.76% may only appear as the leaky-split comparison")]
# Rockfall data is synthetic: any wording that implies real-world data is banned.
REAL_DATA = [
    r"\breal[\s-]world\b",
    r"\breal\s+(data|dataset|datasets|mines?|slopes?|sensors?|incidents?|events|measurements?|readings?|sites?)\b",
    r"\bfield[\s-](data|tested|trials?|validated)",
    r"\bvalidated\b", r"\bdeployed at\b", r"\bactual (mine|mines|slopes?|incidents?)\b",
]
BAD_CODEPOINTS = re.compile(r"[ﬀ-ﬆ�-\x00-\x08\x0b\x0c\x0e-\x1f]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
DOMAIN = re.compile(r"\b(?:[\w-]+\.)+(?:com|org|io|dev|in|ai|net|me|co)(?:/[\w./%-]*)?", re.I)
# A "word" containing an internal hyphen or slash (ROC-AUC, 60/20/20, 7.83/10, ...): the
# template boxes these so they never break mid-token, since a line break there can drop
# the separator on some ATS extractors even when it survives ours.
HYPHEN_TOKEN = re.compile(r"[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)+")


@dataclass
class Report:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def error(self, check, msg):
        self.errors.append(f"[{check}] {msg}")

    def warn(self, check, msg):
        self.warnings.append(f"[{check}] {msg}")

    @property
    def ok(self):
        return not self.errors


# --- helpers ----------------------------------------------------------------------
def numbers(s: str) -> set[str]:
    out = set()
    for tok in NUMBER.findall(s):
        tok = tok.replace(",", "")
        out.add(tok)
        if "." in tok:  # 98.30 == 98.3
            out.add(tok.rstrip("0").rstrip("."))
    return out


def all_strings(obj) -> list[str]:
    """All string values (not keys, ids or fact references) in a nested structure."""
    if isinstance(obj, dict):
        return [s for k, v in obj.items() if k not in ("id", "supports") for s in all_strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in all_strings(v)]
    return [] if obj is None else [str(obj)]


def evidence(facts: dict) -> dict:
    """facts minus the résumé wordings (bullets) and guards: the evidence numbers may come from.
    Excluding bullets means an invented number typed into a bullet is still caught."""
    ev = {k: v for k, v in facts.items()}
    ev["projects"] = [{k: v for k, v in p.items() if k not in ("bullets", "guards")}
                      for p in facts.get("projects", [])]
    return ev


def fact_numbers(facts: dict) -> set[str]:
    return set().union(*(numbers(s) for s in all_strings(evidence(facts))))


def squash(s: str) -> str:
    """Whitespace-free, quote-normalised form used for reading-order matching."""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", "", s).lower()


def hyphen_tokens(doc: Document) -> set[str]:
    """Every hyphenated/slashed token (ROC-AUC, 60/20/20, ...) that will be rendered."""
    texts = [doc.name] + [c["text"] for c in doc.contact]
    for p in doc.projects():
        texts.append(p["name"])
        if p.get("context"):
            texts.append(p["context"])
        texts.extend(p.get("stack") or [])
        if p.get("date"):
            texts.append(p["date"])
        texts.extend(l["text"] for l in p.get("links") or [])
        texts.extend(b["text"] for b in p["bullets"])
    for s in doc.sections:
        if s["kind"] == "education":
            for e in s["entries"]:
                texts.extend(str(v) for v in (e.get("institution"), e.get("degree"),
                                               e.get("date"), e.get("cgpa")) if v)
        elif s["kind"] == "skills":
            for g in s["groups"]:
                texts.extend(g["items"])
    return {m.group(0) for t in texts for m in HYPHEN_TOKEN.finditer(t)}


# --- pre-render checks (on the selected text) ------------------------------------------
def check_claims(facts: dict, doc: Document, rep: Report):
    projects = {p["id"]: p for p in facts.get("projects", [])}
    texts = [doc.name] + [c["text"] for c in doc.contact] + [
        t for p in doc.projects() for t in [p["name"], p.get("context") or ""] + [b["text"] for b in p["bullets"]]
    ]
    for t in texts:
        for pat, why in RETIRED:
            if re.search(pat, t, re.I):
                rep.error("banned", f"{why}: \"{t}\"")

    for p in doc.projects():
        src = projects[p["id"]]
        fact_by_id = {f["id"]: f["text"] for f in src.get("facts", [])}
        if src.get("context"):
            fact_by_id["context"] = src["context"]
        block = " ".join([p["name"], p.get("context") or ""] + [b["text"] for b in p["bullets"]])
        for b in p["bullets"]:
            t = b["text"]
            # provenance: numbers in a bullet must appear in the facts it cites
            sup = b.get("supports") or []
            unknown = [s for s in sup if s not in fact_by_id]
            if not sup or unknown:
                rep.error("provenance", f"{b['id']}: cites no facts or unknown facts {unknown}")
                continue
            allowed = set().union(*(numbers(fact_by_id[s]) for s in sup))
            extra = numbers(t) - allowed
            if extra:
                rep.error("provenance", f"{b['id']}: numbers {sorted(extra)} not in its cited facts {sup}")
            for pat, need, why in CONTEXT_ONLY:
                if re.search(pat, t) and not re.search(need, t, re.I):
                    rep.error("banned", f"{b['id']}: {why}")
            for g in src.get("guards") or []:
                if g["number"] in t and not re.search(g["requires"], t, re.I):
                    rep.error("caveat", f"{b['id']}: {g['number']} needs context /{g['requires']}/ (caveat: {src.get('caveat')})")
        for word in src.get("must_mention") or []:
            if word.lower() not in block.lower():
                rep.error("caveat", f"{p['id']}: selected text must mention '{word}' (caveat: {src.get('caveat')})")
        if "synthetic" in [w.lower() for w in src.get("must_mention") or []] or "rockfall" in p["id"]:
            for pat in REAL_DATA:
                m = re.search(pat, block, re.I)
                if m:
                    rep.error("banned", f"{p['id']}: implies real-world data ('{m.group(0)}'); the data is synthetic")

    # skills must be evidenced by a project stack or an explicit evidence note
    stacks = {s.lower() for p in facts.get("projects", []) for s in p.get("stack", [])}
    for g in facts.get("skills", []):
        for item in g["items"]:
            name = skill_name(item)
            if name.lower() not in stacks and not (isinstance(item, dict) and item.get("evidence")):
                rep.error("skills", f"skill '{name}' is not in any project stack and has no evidence note")


def check_lint(doc: Document, facts: dict, lint: dict, rep: Report, line_counts: dict | None = None):
    ongoing = {p["id"] for p in facts.get("projects", []) if p.get("ongoing")}
    past = set(lint.get("past_verbs", []))
    present = set(lint.get("present_verbs", []))
    max_lines = lint.get("max_lines", 2)
    openers = {}
    for b in doc.bullets():
        m = re.match(r"[A-Za-z-]+", b["text"])
        openers.setdefault(m.group(0).lower() if m else "", []).append(b["id"])
    if lint.get("unique_opening_verbs", True):
        for verb, ids in openers.items():
            if len(ids) > 1:
                rep.error("lint", f"{len(ids)} bullets open with '{verb}': {ids} (max one per page)")
    cap = doc.max_bullets
    for p in doc.projects():
        if cap is not None and len(p["bullets"]) > cap:
            rep.error("lint", f"{p['id']}: {len(p['bullets'])} bullets (max_bullets_per_project is {cap})")
    for p in doc.projects():
        verbs = past | present if p["id"] in ongoing else past
        for b in p["bullets"]:
            t = b["text"]
            first = re.match(r"[A-Za-z-]+", t)
            first = first.group(0) if first else ""
            if first not in verbs:
                tense = "past/present" if p["id"] in ongoing else "past-tense"
                rep.error("lint", f"{b['id']}: should start with a {tense} action verb (got '{first}'); add it to config/lint.yaml if it is one")
            for pat in lint.get("first_person", []):
                if re.search(pat, t, 0 if pat == r"\bI\b" else re.I):
                    rep.error("lint", f"{b['id']}: first person ({pat})")
            for w in lint.get("buzzwords", []):
                if re.search(rf"\b{re.escape(w)}\b", t, re.I):
                    rep.error("lint", f"{b['id']}: buzzword '{w}'")
            if line_counts is not None:
                n = line_counts.get(b["id"])
                if n is not None and n > max_lines:
                    rep.error("lint", f"{b['id']}: renders to {n} lines (max {max_lines})")
        if p["bullets"] and not any(NUMBER.search(b["text"]) for b in p["bullets"]):
            rep.warn("lint", f"{p['id']}: no quantified result among the selected bullets")


# --- post-render checks (on the PDF) ------------------------------------------------
def check_pdf(doc: Document, facts: dict, text: str, pages: int, rep: Report):
    if pages > doc.max_pages:
        rep.error("pages", f"rendered {pages} pages; max_pages is {doc.max_pages}")

    for m in BAD_CODEPOINTS.finditer(text):
        ctx = text[max(0, m.start() - 15): m.end() + 15].replace("\n", " ")
        rep.error("ats", f"bad code point U+{ord(m.group(0)):04X} (ligature/encoding) near \"{ctx}\"")

    lines = {ln.strip().lower() for ln in text.splitlines()}
    for h in doc.headings():
        if h.lower() not in lines:
            rep.error("ats", f"heading '{h}' is not on its own line in the extracted text")

    # ASCII safety: warn on anything outside ASCII except the three allowed marks.
    odd = sorted({c for c in text if ord(c) > 127 and c not in "–•·"})
    for c in odd:
        i = text.index(c)
        ctx = text[max(0, i - 15): i + 15].replace("\n", " ")
        rep.warn("ascii", f"non-ASCII U+{ord(c):04X} '{c}' near \"{ctx}\"")

    hay = squash(text)
    pos = 0
    for frag in doc.reading_order():
        i = hay.find(squash(frag), pos)
        if i < 0:
            where = "missing" if squash(frag) not in hay else "out of order"
            rep.error("ats", f"{where} in extracted text: \"{frag[:70]}\"")
        else:
            pos = i + len(squash(frag))

    # ATS: a hyphenated/slashed token must survive on one line; a line break inside it
    # can drop the separator character on extraction (e.g. "ROC-AUC" -> "ROCAUC").
    line_squashes = [squash(ln) for ln in text.splitlines()]
    for tok in sorted(hyphen_tokens(doc)):
        key = squash(tok)
        if not any(key in ln for ln in line_squashes):
            rep.error("ats", f"'{tok}' is split across a line break in the extracted text")

    # Hard rule 2: every number in the rendered résumé must appear in the facts.
    extra = numbers(text) - fact_numbers(facts)
    for n in sorted(extra):
        rep.error("numbers", f"'{n}' appears in the PDF but not in facts.yaml/private.yaml")

    for pat, why in RETIRED:
        if re.search(pat, text, re.I):
            rep.error("banned", f"{why} (in extracted PDF text)")
    flat = re.sub(r"\s+", " ", text)
    for pat, need, why in CONTEXT_ONLY:
        for m in re.finditer(pat, flat):
            if not re.search(need, flat[max(0, m.start() - 200): m.end() + 50], re.I):
                rep.error("banned", f"{why} (in extracted PDF text)")

    known = {display_url(s).lower() for s in all_strings(facts) if s.startswith("http")}
    email = str(facts["identity"].get("email", "")).lower()
    for m in DOMAIN.finditer(flat):
        d = m.group(0).rstrip("./").lower()
        if d in known or d in email:
            continue
        rep.error("links", f"'{d}' in the PDF does not match any link in facts.yaml")


# Phone-like: 10+ digits allowing +, spaces, dots, dashes and parentheses between them.
PHONE = re.compile(r"(?<![\w.])\+?\(?\d(?:[\s().-]{0,2}\d){9,}(?![\w%])")


def check_public(text: str, facts: dict, rep: Report):
    """The public PDF must contain nothing that looks like a phone number."""
    for m in PHONE.finditer(text):
        rep.error("public", f"phone-number-like text in public PDF: '{m.group(0).strip()}'")
    phone = re.sub(r"\D", "", str((facts.get("_private") or {}).get("phone") or ""))
    if len(phone) >= 7 and phone[-7:] in re.sub(r"\D", "", text):
        rep.error("public", "the private phone number's digits appear in the public PDF")


# --- missing-info report -----------------------------------------------------------
def missing_info(facts: dict, doc: Document, rep: Report) -> list[str]:
    ident = facts.get("identity", {})
    out = []
    for key, why in [("phone", "recruiters (especially in India) expect a phone number with +91"),
                     ("email", "primary contact"), ("location", "city/country for eligibility screening")]:
        v = ident.get(key)
        if not v or str(v).upper().startswith("MISSING"):
            out.append(f"identity.{key}: missing ({why}; phone belongs in data/private.yaml)")
    for p in facts.get("projects", []):
        if not p.get("dates"):
            out.append(f"projects.{p['id']}.dates: missing (month/year shows recency and progression)")
        if not p.get("links"):
            out.append(f"projects.{p['id']}.links: missing")
    for e in facts.get("education", []):
        for key in ["expected_graduation", "cgpa"]:
            if not e.get(key):
                out.append(f"education.{e.get('id')}.{key}: missing")
        if not e.get("coursework"):
            out.append(f"education.{e.get('id')}.coursework: none recorded (optional; relevant ML/maths courses help interns)")
    for key in ["awards", "certifications"]:
        if not facts.get(key):
            out.append(f"{key}: none recorded (don't add any unless real)")
    if not facts.get("experience"):
        out.append("experience: none recorded (section is omitted, not left empty)")
    for w in rep.warnings:
        if "no quantified result" in w:
            out.append(f"{w.split('] ')[1]} (a measured result would strengthen it)")
    out += [f"(from facts.yaml unknown_fill_in_later) {u}" for u in facts.get("unknown_fill_in_later", [])]
    return out
