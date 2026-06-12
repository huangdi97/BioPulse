#!/usr/bin/env python3
"""Extended audit: commented-out code, services without repos, DB ops in services."""
import ast
import os
import re
import sqlite3

ROOT = "/home/hermes/one-cloud-four-ends/cloud"

def find_commented_out_code():
    """Find blocks of commented-out code (>3 consecutive comment lines that look like code)."""
    results = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if "__pycache__" in dirpath:
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except (UnicodeDecodeError):
                continue
            
            # Look for blocks of 3+ consecutive comments that look like code
            comment_block = []
            for i, line in enumerate(lines, 1):
                s = line.strip()
                # Check for commented-out code: lines starting with # that look like actual code
                if s.startswith("#"):
                    # Skip pure comment/docstring lines (no code)
                    code_keywords = ["def ", "class ", "return ", "if ", "for ", "while ", 
                                     "import ", "from ", "self.", "pass", "try:", "except",
                                     "with ", "elif ", "else:", "    ", "\t", "= ", "print",
                                     "raise ", "yield", "break", "continue", "lambda",
                                     "@", "(", "[", "{", "==", "!=", "+=", "-="]
                    content = s.lstrip("# ")
                    is_code = any(kw in content for kw in code_keywords)
                    if is_code:
                        comment_block.append((i, s))
                        continue
                
                # If we hit a non-comment line, check if the block is long enough
                if len(comment_block) >= 3:
                    # Filter out obvious docstring placeholders
                    if any("# " in c[1] and ("def " in c[1] or "class " in c[1]) for c in comment_block):
                        results.append((fp, comment_block[0][0], comment_block[-1][0], 
                                       "\n".join(c[1] for c in comment_block)))
                comment_block = []
            
            # Check final block too
            if len(comment_block) >= 3:
                results.append((fp, comment_block[0][0], comment_block[-1][0],
                               "\n".join(c[1] for c in comment_block)))
    return results

def services_without_repos():
    """Find services that directly use db without a corresponding repository."""
    # List all service files
    service_dir = os.path.join(ROOT, "app", "services")
    repo_dir = os.path.join(ROOT, "app", "repositories")
    
    # Read all repo class names
    repo_classes = set()
    for fn in os.listdir(repo_dir):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        fp = os.path.join(repo_dir, fn)
        try:
            with open(fp, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)
                repo_classes.add(node.name)
    
    print(f"Repository classes found: {len(repo_classes)}")
    for rc in sorted(repo_classes):
        print(f"  {rc}")
    
    print()
    
    # Now check each service for direct DB usage
    # Read all service classes
    service_db_issues = []
    for fn in sorted(os.listdir(service_dir)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        fp = os.path.join(service_dir, fn)
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=fp)
        except (SyntaxError, UnicodeDecodeError):
            continue
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this class uses repository pattern
                has_repo_use = False
                has_db_direct = False
                
                # Check all method bodies
                for item in ast.walk(node):
                    if isinstance(item, ast.Call):
                        if isinstance(item.func, ast.Attribute):
                            if isinstance(item.func.value, ast.Name):
                                # repo.db.execute or similar
                                if item.func.value.id.endswith("_repo") or item.func.value.id.endswith("repo") or "Repository" in item.func.value.id:
                                    has_repo_use = True
                                # self.db.execute or db.execute - direct DB
                                if item.func.value.id in ("self", "db", "conn", "connection") and item.func.attr in ("execute", "commit", "fetchall", "fetchone"):
                                    has_db_direct = True
                    
                    if isinstance(item, ast.Attribute):
                        if isinstance(item.value, ast.Name):
                            if item.value.id == "self" and (item.attr == "db" or item.attr == "_db"):
                                has_db_direct = True
                
                if has_db_direct and not has_repo_use:
                    service_db_issues.append((fp, node.name, node.lineno))
    
    return sorted(service_db_issues)

if __name__ == "__main__":
    print("=" * 70)
    print("COMMENTED-OUT CODE BLOCKS (>3 lines, looking like code)")
    print("=" * 70)
    commented = find_commented_out_code()
    for fp, start, end, block in commented:
        rel = os.path.relpath(fp, ROOT)
        print(f"\n  {rel}:{start}-{end}")
        # Show first and last line
        lines = block.split("\n")
        print(f"    First: {lines[0][:80]}")
        print(f"    Last:  {lines[-1][:80]}")
    if not commented:
        print("  (none found via pattern matching)")
    
    print("\n")
    print("=" * 70)
    print("SERVICES WITH DIRECT DB ACCESS (no repository)")
    print("=" * 70)
    issues = services_without_repos()
    for fp, cls_name, lineno in issues:
        rel = os.path.relpath(fp, ROOT)
        print(f"  {rel}  - class {cls_name}() at line {lineno}")
    if not issues:
        print("  (none found)")
