"""种子数据：Brain记忆系统概念验证——感官/程序记忆预置。"""

import datetime
import json
import sqlite3


def seed_brain_poc(conn: sqlite3.Connection) -> None:
    count_sm = conn.execute("SELECT COUNT(*) FROM sensory_memory").fetchone()[0]
    if count_sm == 0:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ex1 = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO sensory_memory (input_type, raw_content, source, importance, expires_at, created_at) VALUES (?,?,?,?,?,?)",
            ("message", "客户对新产品A的价格提出了质疑，认为定价过高", "chat", 0.75, ex1, now),
        )
        ex2 = (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO sensory_memory (input_type, raw_content, source, importance, expires_at, created_at) VALUES (?,?,?,?,?,?)",
            ("api_event", "商机#1024阶段变更为 'qualify' ，客户表示有采购意向", "crm_webhook", 0.85, ex2, now),
        )
        conn.commit()

    count_pm = conn.execute("SELECT COUNT(*) FROM procedural_memory").fetchone()[0]
    if count_pm == 0:
        procedures = [
            (
                "hcp_visit_flow",
                "HCP拜访流程",
                "标准HCP拜访流程，包含准备、合规检查、执行拜访、记录结果",
                json.dumps(
                    [
                        {"order": 1, "action": "prepare_profile", "desc": "准备HCP画像"},
                        {"order": 2, "action": "check_compliance", "desc": "合规检查"},
                        {"order": 3, "action": "conduct_visit", "desc": "执行拜访"},
                        {"order": 4, "action": "log_result", "desc": "记录结果"},
                    ],
                    ensure_ascii=False,
                ),
                json.dumps(["event:hcp_visit_pending"], ensure_ascii=False),
            ),
            (
                "opportunity_qualify",
                "商机资格验证",
                "商机资格验证流程，检查预算、决策权、需求、时间线",
                json.dumps(
                    [
                        {"order": 1, "action": "check_budget", "desc": "检查预算"},
                        {"order": 2, "action": "verify_authority", "desc": "验证决策权"},
                        {"order": 3, "action": "assess_need", "desc": "评估需求"},
                        {"order": 4, "action": "eval_timeline", "desc": "评估时间线"},
                    ],
                    ensure_ascii=False,
                ),
                json.dumps(["event:opportunity_stage_change", "stage:qualify"], ensure_ascii=False),
            ),
            (
                "compliance_review",
                "合规审查流程",
                "内容合规审查流程，扫描、红线检查、标记违规、生成报告",
                json.dumps(
                    [
                        {"order": 1, "action": "scan_content", "desc": "扫描内容"},
                        {"order": 2, "action": "check_redlines", "desc": "红线检查"},
                        {"order": 3, "action": "flag_violations", "desc": "标记违规"},
                        {"order": 4, "action": "generate_report", "desc": "生成报告"},
                    ],
                    ensure_ascii=False,
                ),
                json.dumps(["event:content_submitted"], ensure_ascii=False),
            ),
        ]
        for key, name, desc, steps, triggers in procedures:
            conn.execute(
                "INSERT INTO procedural_memory (procedure_key, name, description, steps, trigger_conditions) VALUES (?,?,?,?,?)",
                (key, name, desc, steps, triggers),
            )
        conn.commit()
