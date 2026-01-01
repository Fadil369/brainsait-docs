"""
Generate Arabic documentation files from English counterparts.

This script creates placeholder Arabic (.ar.md) files for English markdown files
that don't have Arabic counterparts yet. The generated files include proper
frontmatter and RTL formatting.
"""

import os
import re
from pathlib import Path


def generate_ar_files(root_dir: str) -> None:
    """
    Generate Arabic documentation files for English markdown files.
    
    Args:
        root_dir: Root directory containing documentation files (default: "docs")
    """
    root_path = Path(root_dir)
    for md_file in root_path.rglob("*.md"):
        # Skip Arabic files and special files
        if md_file.name.endswith('.ar.md'):
            continue
        
        # Skip special files
        if md_file.name in ['README.md', 'SUMMARY.md', 'tags.md']:
            continue
        
        ar_file_path = md_file.parent / md_file.name.replace('.md', '.ar.md')
        
        if ar_file_path.exists():
            print(f"Skipping {ar_file_path.relative_to(root_path)} (already exists)")
            continue
        
        print(f"Generating {ar_file_path.relative_to(root_path)}...")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple frontmatter parsing
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            body = frontmatter_match.group(2)
            
            # Add language field if not present
            if 'language:' not in frontmatter:
                frontmatter = f"language: ar\n{frontmatter}"
            
            new_content = f"---\n{frontmatter}\n---\n\n"
            new_content += '!!! info "Translation in Progress / الترجمة قيد الإجراء"\n'
            new_content += '    This content is currently being translated. / هذا المحتوى قيد الترجمة حالياً.\n\n'
            new_content += '<div dir="rtl">\n\n'
            new_content += body  # Copy English content for reference
            new_content += '\n\n</div>'
        else:
            # No frontmatter
            new_content = '---\ntitle: "Translation in Progress"\nlanguage: ar\n---\n\n'
            new_content += '!!! info "Translation in Progress / الترجمة قيد الإجراء"\n'
            new_content += '    This content is currently being translated. / هذا المحتوى قيد الترجمة حالياً.\n\n'
            new_content += '<div dir="rtl">\n\n'
            new_content += content
            new_content += '\n\n</div>'
        
        with open(ar_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

if __name__ == "__main__":
    generate_ar_files("docs")
