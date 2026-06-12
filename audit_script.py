#!/usr/bin/env python3
"""Quick code quality audit script."""
import ast
import os
import sys
from collections import defaultdict

ROOT = "/home/hermes/one-cloud-four-ends/cloud"

def get_package(p):
    """Get the package name for a file path."""
    rel = os.path.relpath(p, ROOT)
    parts = rel.split(os.sep)
    return parts[0] if len(parts) > 1 else "root"

def has_docstring(node):
    """Check if a function/class has a docstring."""
    if not node.body:
        return False
    first = node.body[0]
    return isinstance(first, ast.Expr) and isinstance(first.value, (ast.Str, ast.Constant))

def audit_docstrings():
    """Audit docstring coverage by package."""
    results = defaultdict(lambda: {"funcs": 0, "funcs_doc": 0, "classes": 0, "classes_doc": 0})
    
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if "__pycache__" in dirpath:
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=fp)
            except (SyntaxError, UnicodeDecodeError):
                continue
            
            pkg = get_package(fp)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip dunders and private methods
                    if node.name.startswith("__") and node.name.endswith("__"):
                        continue
                    results[pkg]["funcs"] += 1
                    if has_docstring(node):
                        results[pkg]["funcs_doc"] += 1
                elif isinstance(node, ast.ClassDef):
                    results[pkg]["classes"] += 1
                    if has_docstring(node):
                        results[pkg]["classes_doc"] += 1
    return results

def audit_import_star():
    """Find import * statements."""
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
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if "import *" in stripped and not stripped.startswith("#"):
                    results.append((fp, i, stripped))
    return results

def audit_bare_except():
    """Find bare except: and except Exception without logging or raise."""
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
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # bare except:
                if stripped in ("except:", "except :"):
                    results.append((fp, i, "bare except: (no exception type)"))
                # except Exception: without pass - check next few lines for pass
                elif stripped.startswith("except Exception:") or stripped == "except Exception:":
                    # Check what follows
                    results.append((fp, i, stripped))
    return results

if __name__ == "__main__":
    print("=" * 70)
    print("DOCSTRING COVERAGE BY PACKAGE")
    print("=" * 70)
    doc_results = audit_docstrings()
    for pkg in sorted(doc_results.keys()):
        d = doc_results[pkg]
        if d["funcs"] + d["classes"] == 0:
            continue
        func_pct = (d["funcs_doc"] / d["funcs"] * 100) if d["funcs"] else 100
        class_pct = (d["classes_doc"] / d["classes"] * 100) if d["classes"] else 100
        flag = ""
        if func_pct == 0 and class_pct == 0:
            flag = " *** 0% COVERAGE ***"
        elif func_pct < 10 and class_pct < 10:
            flag = " ** VERY LOW **"
        print(f"  {pkg:30s}  functions: {d['funcs']:3d} ({func_pct:5.1f}%)  classes: {d['classes']:3d} ({class_pct:5.1f}%){flag}")
    
    print()
    print("=" * 70)
    print("IMPORT * STATEMENTS")
    print("=" * 70)
    for fp, ln, line in audit_import_star():
        rel = os.path.relpath(fp, ROOT)
        print(f"  {rel}:{ln}  {line}")
    
    print()
    print("=" * 70)
    print("EXCEPT ISSUES")
    print("=" * 70)
    for fp, ln, line in audit_bare_except():
        rel = os.path.relpath(fp, ROOT)
        print(f"  {rel}:{ln}  {line}")
