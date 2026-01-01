from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _split_target(target: str) -> tuple[str, str]:
    """Split `path#anchor` while preserving anchor."""
    if "#" not in target:
        return target, ""
    path, anchor = target.split("#", 1)
    return path, "#" + anchor


def _is_external(target: str) -> bool:
    return bool(re.match(r"^(https?:|mailto:|#)", target))


def _is_asset(target: str) -> bool:
    return target.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"))


@dataclass
class FixStats:
    files_changed: int = 0
    links_rewritten: int = 0


def rewrite_ar_links(docs_root: Path) -> FixStats:
    """In `.ar.md` files, rewrite internal links from `*.md` -> `*.ar.md` when possible."""
    stats = FixStats()

    for ar_path in docs_root.rglob("*.ar.md"):
        original = ar_path.read_text(encoding="utf-8")
        updated = original

        replacements: list[tuple[str, str]] = []

        for _txt, target in MD_LINK_RE.findall(original):
            if _is_external(target) or _is_asset(target):
                continue

            path_part, anchor = _split_target(target)
            if not path_part.endswith(".md") or path_part.endswith(".ar.md"):
                continue

            # Resolve docs-relative target.
            resolved = (ar_path.parent / path_part).resolve()

            # Only rewrite if resolved is inside docs_root and the `.ar.md` sibling exists.
            try:
                resolved_rel = resolved.relative_to(docs_root.resolve())
            except ValueError:
                continue

            # If the target itself is an Arabic file (but referenced without suffix), handle that too.
            target_ar_rel = resolved_rel.as_posix()[:-3] + ".ar.md"
            target_ar_abs = docs_root / target_ar_rel
            if target_ar_abs.exists():
                new_target = path_part[:-3] + ".ar.md" + anchor
                old_target = path_part + anchor
                replacements.append((old_target, new_target))

        # Apply replacements (simple string replace is safe because we include anchor in match)
        # De-dup to avoid double-counting.
        for old, new in sorted(set(replacements), key=lambda x: (-len(x[0]), x[0])):
            if old in updated:
                updated = updated.replace(old, new)
                stats.links_rewritten += 1

        if updated != original:
            ar_path.write_text(updated, encoding="utf-8")
            stats.files_changed += 1

    return stats


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    docs_root = root / "docs"
    stats = rewrite_ar_links(docs_root)
    print(f"Files changed: {stats.files_changed}")
    print(f"Links rewritten: {stats.links_rewritten}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

