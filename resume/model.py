"""Load facts + private data + config, and select content into a render-ready document.

Selection never creates text: every string in the document is copied from facts.yaml
or private.yaml. The config only picks ids and orders them.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class BuildError(Exception):
    """Raised when inputs are invalid or a check fails."""


def load_yaml(path: Path | str | None) -> dict:
    if path is None:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_facts(facts_path, private_path=None) -> dict:
    facts = load_yaml(facts_path)
    if not facts:
        raise BuildError(f"facts file is missing or empty: {facts_path}")
    private = load_yaml(private_path)
    identity = facts.setdefault("identity", {})
    for key, value in private.items():
        if value not in (None, ""):
            identity[key] = value
    facts["_private"] = private
    return facts


def display_url(url: str) -> str:
    """Visible link text: the URL without scheme, 'www.' or trailing slash."""
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


# Output-only character substitutions (facts.yaml keeps the originals).
_CHAIN = re.compile(r"\d+(?:\s*\([^)]*\))?(?:\s*→\s*\d+(?:\s*\([^)]*\))?){2,}")
_CHARS = {"—": "–", "≥": ">=", "≤": "<=", "’": "'", "‘": "'", "“": '"', "”": '"'}


def ascii_safe(text: str | None) -> str | None:
    """'784 → 128 (ReLU) → 10' -> '784-128-10 (ReLU)'; other '→' -> ' to '; '28×28' -> '28x28'.
    Only characters change; numbers and words stay the same."""
    if text is None:
        return None

    def chain(m):
        nums = re.findall(r"\d+", re.sub(r"\([^)]*\)", "", m.group(0)))
        notes = " ".join(re.findall(r"\([^)]*\)", m.group(0)))
        return "-".join(nums) + (f" {notes}" if notes else "")

    text = _CHAIN.sub(chain, text)
    text = re.sub(r"\s*→\s*", " to ", text)
    text = re.sub(r"(?<=\d)×(?=\d)", "x", text)
    for a, b in _CHARS.items():
        text = text.replace(a, b)
    return text


def skill_name(item) -> str:
    return item["name"] if isinstance(item, dict) else item


@dataclass
class Document:
    name: str
    paper: str
    font_size: float
    max_pages: int
    max_bullets: int | None = None
    contact: list = field(default_factory=list)
    sections: list = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "name": self.name, "paper": self.paper, "font_size": self.font_size,
            "contact": self.contact, "sections": self.sections,
        }

    # --- views used by the checks -------------------------------------------------
    def headings(self) -> list[str]:
        return [s["title"] for s in self.sections]

    def projects(self) -> list[dict]:
        return [p for s in self.sections if s["kind"] == "projects" for p in s["projects"]]

    def bullets(self) -> list[dict]:
        return [b for p in self.projects() for b in p["bullets"]]

    def reading_order(self) -> list[str]:
        """Text fragments that must appear in the extracted PDF, in this order."""
        out = [self.name]
        for s in self.sections:
            out.append(s["title"])
            if s["kind"] == "projects":
                for p in s["projects"]:
                    out.append(p["name"])
                    out.extend(b["text"] for b in p["bullets"])
            elif s["kind"] == "education":
                for e in s["entries"]:
                    out.extend([e["institution"], e["degree"]])
            elif s["kind"] == "skills":
                out.extend(g["label"] for g in s["groups"])
        return out


def _index(items, what):
    out = {}
    for it in items or []:
        if "id" not in it:
            raise BuildError(f"{what} entry without an id: {it}")
        out[it["id"]] = it
    return out


def select(facts: dict, config: dict) -> Document:
    ident = facts["identity"]
    doc = Document(
        name=ident["name"],
        paper=config.get("paper", "a4"),
        font_size=float(config.get("font_size", 10.5)),
        max_pages=int(config.get("max_pages", 1)),
        max_bullets=config.get("max_bullets_per_project"),
    )

    for key in config.get("contact", []):
        value = ident.get(key)
        if not value or str(value).upper().startswith("MISSING"):
            continue
        value = str(value)
        if value.startswith("http"):
            doc.contact.append({"text": display_url(value), "url": value})
        elif key == "email":
            doc.contact.append({"text": value, "url": f"mailto:{value}"})
        else:
            doc.contact.append({"text": value, "url": None})

    headings = config.get("headings", {})
    projects = _index(facts.get("projects"), "project")
    skills = _index(facts.get("skills"), "skill group")

    for kind in config.get("sections", []):
        title = headings.get(kind, kind.title())
        if kind == "education":
            entries = []
            for e in facts.get("education", []):
                date = e.get("expected_graduation")
                entries.append({
                    "institution": e["institution"], "degree": e["degree"],
                    "date": f"Expected {date}" if date else None,
                    "cgpa": e.get("cgpa") if config.get("show_cgpa", True) else None,
                })
            doc.sections.append({"kind": kind, "title": title, "entries": entries})
        elif kind == "projects":
            chosen = []
            for sel in config.get("projects", []):
                pid = sel["id"] if isinstance(sel, dict) else sel
                if pid not in projects:
                    raise BuildError(f"config selects unknown project '{pid}'")
                p = projects[pid]
                bullets = _index(p.get("bullets"), f"bullet in {pid}")
                ids = sel.get("bullets") if isinstance(sel, dict) else None
                ids = ids if ids is not None else list(bullets)
                missing = [b for b in ids if b not in bullets]
                if missing:
                    raise BuildError(f"config selects unknown bullets {missing} in project '{pid}'")
                n_links = sel.get("links", 1) if isinstance(sel, dict) else 1
                safe = ascii_safe if config.get("ascii_output") else (lambda t: t)
                # A bullet that cites `context` already says it; don't repeat it in the header.
                context_in_bullet = any("context" in (bullets[b].get("supports") or []) for b in ids)
                chosen.append({
                    "id": pid,
                    "name": safe(p["name"]),
                    "context": None if context_in_bullet else safe(p.get("context")),
                    "stack": list(p.get("stack", [])),
                    "date": p.get("dates"),
                    "links": [{"text": display_url(u), "url": u} for u in p.get("links", [])[:n_links]],
                    "bullets": [{**copy.deepcopy(bullets[b]), "id": f"{pid}/{b}", "text": safe(bullets[b]["text"])}
                                for b in ids],
                })
            doc.sections.append({"kind": kind, "title": title, "projects": chosen})
        elif kind == "skills":
            groups = []
            for gid in config.get("skills", list(skills)):
                if gid not in skills:
                    raise BuildError(f"config selects unknown skill group '{gid}'")
                g = skills[gid]
                items = [skill_name(i) for i in g["items"]]
                prio = [x.lower() for x in config.get("skills_priority", [])]
                items.sort(key=lambda n: prio.index(n.lower()) if n.lower() in prio else len(prio))
                groups.append({"label": g["label"], "items": items})
            doc.sections.append({"kind": kind, "title": title, "groups": groups})
        elif kind == "experience":
            if facts.get("experience"):
                raise BuildError("experience rendering is not implemented yet; remove it from sections")
            # Empty experience is never rendered (research rule 4.3).
        else:
            raise BuildError(f"unknown section '{kind}'")
    return doc
