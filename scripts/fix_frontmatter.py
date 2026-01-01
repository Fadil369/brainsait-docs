#!/usr/bin/env python3
"""
Fix Frontmatter Issues
======================

Adds missing language fields and fixes frontmatter consistency.
"""

import re
from pathlib import Path

def fix_arabic_frontmatter(file_path: Path):
    """Add language: ar to Arabic files missing it."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if frontmatter exists
    frontmatter_match = re.match(r'^(---\n)(.*?)(\n---\n)', content, re.DOTALL)
    
    if not frontmatter_match:
        # No frontmatter - add it
        frontmatter = f"---\ntitle: \"{file_path.stem.replace('.ar', '')}\"\nlanguage: ar\n---\n\n"
        new_content = frontmatter + content
    else:
        frontmatter_start = frontmatter_match.group(1)
        frontmatter_body = frontmatter_match.group(2)
        frontmatter_end = frontmatter_match.group(3)
        body = content[len(frontmatter_match.group(0)):]
        
        # Check if language field exists
        if 'language:' not in frontmatter_body:
            # Add language field after title if exists, otherwise at the end
            if 'title:' in frontmatter_body:
                # Insert after title
                frontmatter_body = re.sub(
                    r'(title:[^\n]+\n)',
                    r'\1language: ar\n',
                    frontmatter_body,
                    count=1
                )
            else:
                # Add at the beginning
                frontmatter_body = 'language: ar\n' + frontmatter_body
        
        new_content = frontmatter_start + frontmatter_body + frontmatter_end + body
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def fix_missing_frontmatter(file_path: Path):
    """Add basic frontmatter to files missing it."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has frontmatter
    if content.startswith('---'):
        return False
    
    # Generate title from filename
    title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
    if file_path.name.endswith('.ar.md'):
        title = title.replace('.Ar', '')
        language = 'ar'
    else:
        language = 'en'
    
    frontmatter = f"---\ntitle: \"{title}\"\nlanguage: {language}\n---\n\n"
    new_content = frontmatter + content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    docs_dir = Path("docs")
    
    # Fix Arabic files
    print("Fixing Arabic file frontmatter...")
    ar_files = list(docs_dir.rglob("*.ar.md"))
    fixed_count = 0
    
    for ar_file in ar_files:
        try:
            with open(ar_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if language field is missing
            if 'language:' not in content or ('language:' in content and 'language: ar' not in content):
                fix_arabic_frontmatter(ar_file)
                fixed_count += 1
                print(f"  Fixed: {ar_file.relative_to(docs_dir)}")
        except Exception as e:
            print(f"  Error fixing {ar_file}: {e}")
    
    print(f"\nFixed {fixed_count} Arabic files")
    
    # Fix files missing frontmatter (excluding special files)
    print("\nFixing files missing frontmatter...")
    special_files = {'README.md', 'SUMMARY.md', 'tags.md', 'MAINTENANCE_GUIDE.md', 
                     'SEO_GUIDE.md', 'ACCESSIBILITY_TESTING.md'}
    
    md_files = [f for f in docs_dir.rglob("*.md") 
                if f.name not in special_files and not f.name.endswith('.ar.md')]
    
    fixed_frontmatter = 0
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('---'):
                fix_missing_frontmatter(md_file)
                fixed_frontmatter += 1
                print(f"  Added frontmatter: {md_file.relative_to(docs_dir)}")
        except Exception as e:
            print(f"  Error fixing {md_file}: {e}")
    
    print(f"\nFixed {fixed_frontmatter} files missing frontmatter")
    print("\n✅ Frontmatter fixes complete!")

if __name__ == "__main__":
    main()
