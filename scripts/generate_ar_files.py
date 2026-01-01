from __future__ import annotations

import re
from pathlib import Path

# Minimal frontmatter parsing (avoid new deps)
FRONTMATTER_RE = re.compile(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$")


def _extract_title(frontmatter: str) -> str | None:
    """Extract a YAML `title:` value with a light heuristic (no YAML deps)."""
    m = re.search(r"^title:\s*(.+)\s*$", frontmatter, flags=re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")


def generate_ar_files(root_dir: str = "docs") -> None:
    """Generate Arabic stub files using the `.ar.md` suffix.

    This generator intentionally does NOT copy English body content into the Arabic
    file (to avoid mixed-language pages). Instead, it creates a structured Arabic
    stub and links back to the English source.
    """

    root = Path(root_dir)
    for path in root.rglob("*.md"):
        if path.name.endswith(".ar.md"):
            continue

        ar_path = path.with_name(path.name[:-3] + ".ar.md")
        if ar_path.exists():
            print(f"Skipping {ar_path} (already exists)")
            continue

        print(f"Generating {ar_path}...")
        content = path.read_text(encoding="utf-8")

        frontmatter = ""
        m = FRONTMATTER_RE.match(content)
        if m:
            frontmatter = m.group(1)

        title = _extract_title(frontmatter) or path.stem.replace("_", " ")

        # Preserve existing frontmatter keys when present; add minimal AR metadata.
        if frontmatter:
            ar_frontmatter = frontmatter
            if re.search(r"^language:\s*", ar_frontmatter, flags=re.MULTILINE) is None:
                ar_frontmatter += "\nlanguage: ar"
            if re.search(r"^translation_status:\s*", ar_frontmatter, flags=re.MULTILINE) is None:
                ar_frontmatter += "\ntranslation_status: draft"
        else:
            ar_frontmatter = f'title: "{title}"\nlanguage: ar\ntranslation_status: draft'

        # MkDocs resolves relative links from current page location; we keep it simple.
        rel_en = path.relative_to(root).as_posix()

        new_content = (
            f"---\n{ar_frontmatter}\n---\n\n"
            '!!! info "الترجمة قيد الإجراء"\n'
            f"    هذه الصفحة قيد الترجمة. راجع النسخة الإنجليزية مؤقتًا: [`{rel_en}`]({rel_en})\n\n"
            '<div dir="rtl" lang="ar" markdown>\n\n'
            f"# {title}\n\n"
            "## نظرة عامة\n\n"
            "(قيد الإعداد)\n\n"
            "## المحتوى الأساسي\n\n"
            "(قيد الإعداد)\n\n"
            "---\n\n"
            "**التحكم في المستند**\n"
            "- الحالة: مسودة ترجمة\n"
            "- آخر تحديث: (أضف التاريخ)\n\n"
            "</div>\n"
        )

        ar_path.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    generate_ar_files()

