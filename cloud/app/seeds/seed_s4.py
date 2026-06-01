import json
import sqlite3


def seed_s4(conn: sqlite3.Connection) -> None:
    count_pcj = conn.execute("SELECT COUNT(*) FROM privacy_compute_jobs").fetchone()[0]
    count_fr = conn.execute("SELECT COUNT(*) FROM federated_rounds").fetchone()[0]
    count_ncl = conn.execute("SELECT COUNT(*) FROM nmpa_compliance_logs").fetchone()[0]
    if count_pcj > 0 and count_fr > 0 and count_ncl > 0:
        return
    now = "2026-05-25 10:00:00"

    if count_pcj == 0:
        conn.execute(
            "INSERT INTO privacy_compute_jobs (job_id, compute_type, sensitivity_level, "
            "data_summary, selected_scheme, status, created_at) VALUES (?,?,?,?,?,?,?)",
            ("pc:test-001", "hybrid", "high",
             '{"records":1000,"features":["hcp_prescription","visit_freq"]}',
             "DP+FL+HE", "completed", now))

    if count_fr == 0:
        conn.execute(
            "INSERT INTO federated_rounds (round_id, model_name, round_number, participant_count, "
            "aggregation_method, status, created_at, completed_at) VALUES (?,?,?,?,?,?,?,?)",
            ("fl:test-001", "prescription_model", 1, 3, "fed_avg", "completed", now, now))

    if count_ncl == 0:
        conn.execute(
            "INSERT INTO nmpa_compliance_logs (log_id, document_type, content_summary, check_result, "
            "violations_found, violation_details, human_review_required, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            ("nmpa:test-001", "promotion", "推广材料含'首个'、'最佳'等绝对化用语", "fail", 2,
             '["绝对化用语:首个","绝对化用语:最佳"]', 1, now))
        conn.execute(
            "INSERT INTO nmpa_compliance_logs (log_id, document_type, content_summary, check_result, "
            "violations_found, violation_details, human_review_required, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            ("nmpa:test-002", "report", "合规报告内容无违规", "pass", 0, "[]", 0, now))

    conn.commit()
