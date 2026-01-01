from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


class _IgnoreUnknownTagsLoader(yaml.SafeLoader):
    """MkDocs configs can include python tags (e.g., pymdownx). Ignore them."""


def _ignore_unknown(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


_IgnoreUnknownTagsLoader.add_multi_constructor("", _ignore_unknown)


ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
FRONTMATTER_RE = re.compile(r"^---\n[\s\S]*?\n---\n")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _strip_code(text: str) -> str:
    text = CODE_FENCE_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    return text


@dataclass(frozen=True)
class AuditResult:
    nav_pages: int
    missing_nav_files: list[str]
    missing_arabic_counterparts: list[tuple[str, str]]
    missing_frontmatter: list[str]
    weak_arabic_pages: list[tuple[str, float]]
    arabic_pages_linking_to_en_md: dict[str, list[str]]


def _iter_nav_files(node) -> Iterable[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from _iter_nav_files(item)
    elif isinstance(node, dict):
        for _, v in node.items():
            yield from _iter_nav_files(v)


def _arabic_ratio_of_letters(text: str) -> float:
    t = _strip_code(text)
    a = len(ARABIC_RE.findall(t))
    l = len(LATIN_RE.findall(t))
    return a / max(a + l, 1)


def audit_repo(root: Path, arabic_ratio_threshold: float = 0.20) -> AuditResult:
    docs_root = root / "docs"
    mkdocs_path = root / "mkdocs.yml"

    mkdocs = yaml.load(mkdocs_path.read_text(encoding="utf-8"), Loader=_IgnoreUnknownTagsLoader)
    nav = mkdocs.get("nav", [])
    nav_files = [p for p in _iter_nav_files(nav) if isinstance(p, str) and p.endswith(".md")]

    existing = {p.relative_to(docs_root).as_posix() for p in docs_root.rglob("*.md")}

    missing_nav_files = [p for p in nav_files if p not in existing]

    missing_arabic_counterparts: list[tuple[str, str]] = []
    for p in nav_files:
        if p.endswith(".ar.md"):
            continue
        ar = p[:-3] + ".ar.md"
        if ar not in existing:
            missing_arabic_counterparts.append((p, ar))

    missing_frontmatter: list[str] = []
    weak_arabic_pages: list[tuple[str, float]] = []
    arabic_pages_linking_to_en_md: dict[str, list[str]] = {}

    for p in nav_files:
        if p.endswith(".ar.md"):
            continue

        en_path = docs_root / p
        ar_rel = p[:-3] + ".ar.md"
        ar_path = docs_root / ar_rel

        en = en_path.read_text(encoding="utf-8")
        ar = ar_path.read_text(encoding="utf-8")

        if not FRONTMATTER_RE.match(en):
            missing_frontmatter.append(p)
        if not FRONTMATTER_RE.match(ar):
            missing_frontmatter.append(ar_rel)

        ratio = _arabic_ratio_of_letters(ar)
        if ratio < arabic_ratio_threshold:
            weak_arabic_pages.append((ar_rel, ratio))

        # Arabic link hygiene: internal `.md` links should point to `.ar.md` if available.
        bad_targets: list[str] = []
        for _txt, target in MD_LINK_RE.findall(ar):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            if target.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
                continue
            if target.endswith(".md") and not target.endswith(".ar.md"):
                bad_targets.append(target)
        if bad_targets:
            arabic_pages_linking_to_en_md[ar_rel] = bad_targets

    return AuditResult(
        nav_pages=len(nav_files),
        missing_nav_files=missing_nav_files,
        missing_arabic_counterparts=missing_arabic_counterparts,
        missing_frontmatter=missing_frontmatter,
        weak_arabic_pages=sorted(weak_arabic_pages, key=lambda x: x[1]),
        arabic_pages_linking_to_en_md=arabic_pages_linking_to_en_md,
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    res = audit_repo(root)

    print(f"Nav pages: {res.nav_pages}")
    print(f"Missing nav files: {len(res.missing_nav_files)}")
    for p in res.missing_nav_files:
        print(f"  MISSING: {p}")

    print(f"Missing Arabic counterparts: {len(res.missing_arabic_counterparts)}")
    for en, ar in res.missing_arabic_counterparts:
        print(f"  NO_AR: {en} -> expected {ar}")

    print(f"Missing frontmatter (nav pages, both langs): {len(res.missing_frontmatter)}")
    if res.missing_frontmatter:
        for p in res.missing_frontmatter[:50]:
            print(f"  NO_FM: {p}")
        if len(res.missing_frontmatter) > 50:
            print("  ... truncated ...")

    print(f"Arabic pages likely not translated (ratio < 0.20): {len(res.weak_arabic_pages)}")
    for p, ratio in res.weak_arabic_pages[:25]:
        print(f"  WEAK_AR: {p} (ratio={ratio:.3f})")
    if len(res.weak_arabic_pages) > 25:
        print("  ... truncated ...")

    bad_link_count = sum(len(v) for v in res.arabic_pages_linking_to_en_md.values())
    print(f"Arabic internal links pointing to `.md` (not `.ar.md`): {bad_link_count} links across {len(res.arabic_pages_linking_to_en_md)} pages")
    for p, targets in list(res.arabic_pages_linking_to_en_md.items())[:25]:
        uniq = sorted(set(targets))
        print(f"  BAD_LINKS: {p} -> {', '.join(uniq[:12])}{' ...' if len(uniq) > 12 else ''}")
    if len(res.arabic_pages_linking_to_en_md) > 25:
        print("  ... truncated ...")

    # This audit is informational by default; use CI policies to decide pass/fail.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

