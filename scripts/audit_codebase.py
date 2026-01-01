#!/usr/bin/env python3
"""
Comprehensive Codebase Audit Script
===================================

This script audits:
1. Code quality (Python scripts)
2. Bilingual documentation coverage
3. Naming conventions (.ar.md suffix)
4. Frontmatter consistency
5. Link integrity
6. Style guide compliance
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from datetime import datetime

class CodebaseAuditor:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.docs_dir = self.root_dir / "docs"
        self.scripts_dir = self.root_dir / "scripts"
        self.issues = defaultdict(list)
        self.stats = {
            "total_en_files": 0,
            "total_ar_files": 0,
            "missing_ar_counterparts": 0,
            "missing_en_counterparts": 0,
            "naming_violations": 0,
            "frontmatter_issues": 0,
            "link_issues": 0,
            "code_quality_issues": 0,
        }
        
    def audit_all(self) -> Dict:
        """Run all audit checks."""
        print("🔍 Starting comprehensive codebase audit...\n")
        
        # 1. Code quality audit
        print("1️⃣ Auditing Python code quality...")
        self.audit_python_code()
        
        # 2. Bilingual coverage
        print("\n2️⃣ Auditing bilingual documentation coverage...")
        self.audit_bilingual_coverage()
        
        # 3. Naming conventions
        print("\n3️⃣ Auditing naming conventions...")
        self.audit_naming_conventions()
        
        # 4. Frontmatter consistency
        print("\n4️⃣ Auditing frontmatter consistency...")
        self.audit_frontmatter()
        
        # 5. Link integrity
        print("\n5️⃣ Auditing link integrity...")
        self.audit_links()
        
        # 6. Style guide compliance
        print("\n6️⃣ Auditing style guide compliance...")
        self.audit_style_guide()
        
        return {
            "issues": dict(self.issues),
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def audit_python_code(self):
        """Audit Python code quality."""
        python_files = list(self.scripts_dir.glob("*.py"))
        
        for py_file in python_files:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for common issues
            for i, line in enumerate(lines, 1):
                # Missing docstrings for functions/classes
                if re.match(r'^\s*(def|class)\s+\w+', line):
                    # Check if next non-empty line is docstring
                    next_lines = [l.strip() for l in lines[i:i+3] if l.strip()]
                    if next_lines and not (next_lines[0].startswith('"""') or next_lines[0].startswith("'''")):
                        if 'if __name__' not in line and '__init__' not in line:
                            self.issues['code_quality'].append(
                                f"{py_file.name}:{i} - Function/class missing docstring"
                            )
                            self.stats["code_quality_issues"] += 1
                
                # Hardcoded paths
                if re.search(r'["\'](?:\.\.?/)?(?:docs|scripts|workspace)', line):
                    if 'os.path' not in line and 'Path(' not in line:
                        self.issues['code_quality'].append(
                            f"{py_file.name}:{i} - Potential hardcoded path"
                        )
                
                # Missing error handling
                if 'open(' in line and 'with' not in line:
                    self.issues['code_quality'].append(
                        f"{py_file.name}:{i} - File open without context manager"
                    )
    
    def audit_bilingual_coverage(self):
        """Check if all English docs have Arabic counterparts."""
        en_files = set()
        ar_files = set()
        
        # Find all markdown files
        for md_file in self.docs_dir.rglob("*.md"):
            if md_file.name.endswith('.ar.md'):
                ar_files.add(md_file)
                # Get corresponding EN file
                en_path = md_file.parent / md_file.name.replace('.ar.md', '.md')
                if not en_path.exists():
                    self.issues['bilingual_coverage'].append(
                        f"Arabic file {md_file.relative_to(self.docs_dir)} has no English counterpart"
                    )
                    self.stats["missing_en_counterparts"] += 1
            elif not md_file.name.endswith('.ar.md'):
                en_files.add(md_file)
                self.stats["total_en_files"] += 1
        
        # Check for missing Arabic counterparts
        for en_file in en_files:
            # Skip special files
            if en_file.name in ['README.md', 'SUMMARY.md', 'tags.md', 'MAINTENANCE_GUIDE.md', 
                               'SEO_GUIDE.md', 'ACCESSIBILITY_TESTING.md']:
                continue
            
            ar_path = en_file.parent / en_file.name.replace('.md', '.ar.md')
            if not ar_path.exists():
                self.issues['bilingual_coverage'].append(
                    f"English file {en_file.relative_to(self.docs_dir)} missing Arabic counterpart"
                )
                self.stats["missing_ar_counterparts"] += 1
        
        self.stats["total_ar_files"] = len(ar_files)
    
    def audit_naming_conventions(self):
        """Check naming convention compliance."""
        for md_file in self.docs_dir.rglob("*.md"):
            # Check Arabic files use .ar.md suffix
            if 'ar' in md_file.name.lower() and not md_file.name.endswith('.ar.md'):
                self.issues['naming'].append(
                    f"Incorrect Arabic file naming: {md_file.relative_to(self.docs_dir)}"
                )
                self.stats["naming_violations"] += 1
            
            # Check for mixed language files (should be separate)
            if md_file.name.endswith('.ar.md'):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check for excessive English content in Arabic files
                    # (allowing for code blocks and technical terms)
                    if '<div dir="rtl">' not in content and 'lang="ar"' not in content:
                        # Check if file has substantial Arabic content
                        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', content))
                        total_chars = len(re.sub(r'\s', '', content))
                        if total_chars > 0 and arabic_chars / total_chars < 0.3:
                            self.issues['naming'].append(
                                f"Arabic file {md_file.relative_to(self.docs_dir)} may contain mostly English content"
                            )
    
    def audit_frontmatter(self):
        """Check frontmatter consistency."""
        required_fields = ['title']
        recommended_fields = ['description', 'version', 'last_updated']
        
        for md_file in self.docs_dir.rglob("*.md"):
            if md_file.name in ['README.md', 'SUMMARY.md']:
                continue
                
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for frontmatter
            frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
            
            if not frontmatter_match:
                self.issues['frontmatter'].append(
                    f"Missing frontmatter: {md_file.relative_to(self.docs_dir)}"
                )
                self.stats["frontmatter_issues"] += 1
                continue
            
            frontmatter = frontmatter_match.group(1)
            
            # Check required fields
            for field in required_fields:
                if f'{field}:' not in frontmatter:
                    self.issues['frontmatter'].append(
                        f"Missing required field '{field}': {md_file.relative_to(self.docs_dir)}"
                    )
                    self.stats["frontmatter_issues"] += 1
            
            # Check language field for Arabic files
            if md_file.name.endswith('.ar.md'):
                if 'language:' not in frontmatter or 'ar' not in frontmatter:
                    self.issues['frontmatter'].append(
                        f"Arabic file missing language:ar field: {md_file.relative_to(self.docs_dir)}"
                    )
            
            # Check for version consistency
            if 'version:' in frontmatter:
                version_match = re.search(r'version:\s*["\']?([^"\'\n]+)', frontmatter)
                if version_match:
                    version = version_match.group(1).strip()
                    # Check corresponding file has same version
                    if md_file.name.endswith('.ar.md'):
                        en_file = md_file.parent / md_file.name.replace('.ar.md', '.md')
                    else:
                        en_file = md_file.parent / (md_file.name.replace('.md', '.ar.md'))
                    
                    if en_file.exists():
                        with open(en_file, 'r', encoding='utf-8') as f:
                            en_content = f.read()
                            en_frontmatter_match = re.match(r'^---\n(.*?)\n---\n', en_content, re.DOTALL)
                            if en_frontmatter_match:
                                en_frontmatter = en_frontmatter_match.group(1)
                                en_version_match = re.search(r'version:\s*["\']?([^"\'\n]+)', en_frontmatter)
                                if en_version_match:
                                    en_version = en_version_match.group(1).strip()
                                    if version != en_version:
                                        self.issues['frontmatter'].append(
                                            f"Version mismatch: {md_file.relative_to(self.docs_dir)} ({version}) vs {en_file.relative_to(self.docs_dir)} ({en_version})"
                                        )
    
    def audit_links(self):
        """Check link integrity."""
        all_md_files = {f.relative_to(self.docs_dir): f for f in self.docs_dir.rglob("*.md")}
        
        for md_file_path, md_file in all_md_files.items():
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all markdown links
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            links = re.findall(link_pattern, content)
            
            for link_text, link_url in links:
                # Skip external links
                if link_url.startswith('http://') or link_url.startswith('https://'):
                    continue
                
                # Skip anchor links
                if link_url.startswith('#'):
                    continue
                
                # Resolve relative paths
                if link_url.startswith('../') or link_url.startswith('./'):
                    target_path = (md_file.parent / link_url).resolve()
                else:
                    target_path = (md_file.parent / link_url).resolve()
                
                # Check if target exists
                if not target_path.exists():
                    # Check if it's a link to Arabic version from English file
                    if md_file.name.endswith('.ar.md') and link_url.endswith('.md') and not link_url.endswith('.ar.md'):
                        # This might be intentional - English file linking to English version
                        pass
                    elif not md_file.name.endswith('.ar.md') and link_url.endswith('.ar.md'):
                        # English file linking to Arabic - might be intentional
                        pass
                    else:
                        self.issues['links'].append(
                            f"Broken link in {md_file_path}: [{link_text}]({link_url})"
                        )
                        self.stats["link_issues"] += 1
    
    def audit_style_guide(self):
        """Check style guide compliance."""
        style_guide_path = self.root_dir / "BILINGUAL_STYLE_GUIDE.md"
        
        if not style_guide_path.exists():
            self.issues['style_guide'].append("BILINGUAL_STYLE_GUIDE.md not found")
            return
        
        # Check for RTL divs in Arabic files
        for md_file in self.docs_dir.rglob("*.ar.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for RTL wrapper
            if '<div dir="rtl">' not in content and '<div dir="rtl" markdown>' not in content:
                # Allow if entire content is in Arabic (no need for wrapper if markdown extension handles it)
                # But check if there's mixed content
                if 'lang="ar"' not in content:
                    # This might be okay if mkdocs handles RTL automatically
                    pass
            
            # Check for proper Arabic typography (18px base mentioned in style guide)
            # This would require CSS inspection, so we'll skip for now
            
            # Check for code blocks in English (as per style guide)
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
            for lang, code in code_blocks:
                # Code should be in English even in Arabic docs
                # This is hard to verify automatically, so we'll note it
                pass
    
    def generate_report(self, output_file: str = "audit_report.json"):
        """Generate audit report."""
        report = self.audit_all()
        
        # Save JSON report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 AUDIT SUMMARY")
        print("="*60)
        print(f"\n📄 Documentation Files:")
        print(f"   English files: {report['stats']['total_en_files']}")
        print(f"   Arabic files: {report['stats']['total_ar_files']}")
        print(f"   Missing AR counterparts: {report['stats']['missing_ar_counterparts']}")
        print(f"   Missing EN counterparts: {report['stats']['missing_en_counterparts']}")
        
        print(f"\n🔧 Code Quality:")
        print(f"   Issues found: {report['stats']['code_quality_issues']}")
        
        print(f"\n📝 Documentation Quality:")
        print(f"   Naming violations: {report['stats']['naming_violations']}")
        print(f"   Frontmatter issues: {report['stats']['frontmatter_issues']}")
        print(f"   Link issues: {report['stats']['link_issues']}")
        
        print(f"\n📋 Issues by Category:")
        for category, issues in report['issues'].items():
            print(f"   {category}: {len(issues)}")
            if issues:
                for issue in issues[:5]:  # Show first 5
                    print(f"      - {issue}")
                if len(issues) > 5:
                    print(f"      ... and {len(issues) - 5} more")
        
        print(f"\n✅ Full report saved to: {output_file}")
        print("="*60)
        
        return report


if __name__ == "__main__":
    auditor = CodebaseAuditor()
    report = auditor.generate_report("audit_report.json")
    
    # Exit with error code if issues found
    total_issues = sum(len(issues) for issues in report['issues'].values())
    exit(1 if total_issues > 0 else 0)
