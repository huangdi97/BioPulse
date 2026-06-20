"""Report generation for evaluation results."""

import json


def format_report(report: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append(f"Eval Report — suite: {report.get('suite', 'unknown')}")
    lines.append("=" * 60)
    lines.append(f"Total: {report.get('total', 0)}  Passed: {report.get('passed', 0)}  Failed: {report.get('failed', 0)}")
    lines.append("")
    for r in report.get("results", []):
        passed_char = "PASS" if r.get("passed") is True else "FAIL" if r.get("passed") is False else "DRYR"
        lines.append(f"  [{passed_char}] {r.get('agent_key', '?')} — {r.get('goal', '?')[:60]}")
        if r.get("passed") is False:
            lines.append(f"        status={r.get('status')}  expected={r.get('expected', {}).get('status')}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_json(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def ci_exit(report: dict, threshold: float = 0.9) -> int:
    total = report.get("total", 0)
    if total == 0:
        return 0
    passed = report.get("passed", 0)
    rate = passed / total
    return 0 if rate >= threshold else 1
