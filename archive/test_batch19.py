#!/usr/bin/env python3
"""Batch 19 comprehensive test script."""

import json
import urllib.error
import urllib.request

BASE = "http://localhost:8000"


def api(method, path, data=None, token=None):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


# Step 1: Register + Login
print("=== Setup ===")
r = api(
    "POST",
    "/auth/register",
    {"username": "admin", "password": "admin123", "role": "admin"},
)
print(f"Register: {r}")

r = api("POST", "/auth/login", {"username": "admin", "password": "admin123"})
token = r["data"]["access_token"]
print(f"Login OK, token: {token[:20]}...")

# === 19-1: 审计日志 ===
print("\n=== 19-1: 审计日志 ===")

r = api(
    "POST",
    "/audit/logs",
    {"user_id": 1, "action": "login", "entity_type": "user", "source_end": "cloud"},
    token,
)
print(f"1. Create audit log: {r}")
assert r["code"] == 0, f"FAIL: {r}"

r = api("GET", "/audit/logs", token=token)
print(f"2. List audit logs: total={r['data']['total']}")
assert r["code"] == 0 and r["data"]["total"] >= 1

r = api("GET", "/audit/logs/stats", token=token)
print(f"3. Audit stats: {r}")
assert r["code"] == 0

print("✅ 19-1 审计日志 全部通过")

# === 19-2: 通知系统 ===
print("\n=== 19-2: 通知系统 ===")

r = api(
    "POST",
    "/notifications/templates",
    {
        "name": "compliance_alert",
        "title_template": "合规检查提醒: {title}",
        "body_template": "内容 {title} 评分 {score}",
        "category": "compliance",
    },
    token,
)
print(f"1. Create template: {r}")
assert r["code"] == 0
tmpl_id = r["data"]["id"]

r = api("GET", "/notifications/templates", token=token)
print(f"2. List templates: count={len(r['data'])}")
assert r["code"] == 0

r = api("GET", f"/notifications/templates/{tmpl_id}", token=token)
print(f"3. Get template: {r['data']['name']}")
assert r["code"] == 0

r = api("PATCH", f"/notifications/templates/{tmpl_id}", {"category": "alert"}, token)
print(f"4. Update template: {r}")
assert r["code"] == 0

r = api(
    "POST",
    "/notifications/send",
    {
        "user_id": 1,
        "template_name": "compliance_alert",
        "context": {"title": "测试文章", "score": "0.8"},
    },
    token,
)
print(f"5. Send notification: {r}")
assert r["code"] == 0
notif_id = r["data"]["id"]

r = api("GET", "/notifications/", token=token)
print(f"6. List notifications: total={r['data']['total']}")
assert r["code"] == 0

r = api("PATCH", f"/notifications/{notif_id}/read", token=token)
print(f"7. Mark read: {r}")
assert r["code"] == 0

r = api("GET", "/notifications/unread-count", token=token)
print(f"8. Unread count: {r}")
assert r["code"] == 0

print("✅ 19-2 通知系统 全部通过")

# === 19-3: 通知客户端集成 ===
print("\n=== 19-3: 通知客户端 ===")

r = api(
    "POST",
    "/contents/",
    {
        "title": "测试违规内容",
        "body": "这款产品绝对安全，无副作用，可以根治所有疾病",
        "category": "medical",
    },
    token,
)
print(f"Create non-compliant content: status={r['data']['status']}, score={r['data']['compliance_score']}")
assert r["code"] == 0
assert r["data"]["compliance_score"] < 1.0

r = api("GET", "/notifications/unread-count", token=token)
print(f"Notification count after content creation: {r}")
assert r["code"] == 0
assert r["data"]["unread_count"] >= 1

print("✅ 19-3 通知客户端 全部通过")

# === 19-4: 看板管理 ===
print("\n=== 19-4: 看板管理 ===")

r = api("POST", "/boards/", {"name": "我的看板", "description": "测试看板"}, token)
print(f"1. Create board: {r}")
assert r["code"] == 0
board_id = r["data"]["id"]

r = api("GET", "/boards/", token=token)
print(f"2. List boards: count={len(r['data'])}")
assert r["code"] == 0

r = api("GET", f"/boards/{board_id}", token=token)
print(f"3. Get board: {r['data']['name']}")
assert r["code"] == 0

r = api("PATCH", f"/boards/{board_id}", {"description": "更新描述"}, token)
print(f"4. Update board: {r}")
assert r["code"] == 0

r = api(
    "POST",
    f"/boards/{board_id}/tasks",
    {"title": "完成任务1", "priority": "high", "status": "todo"},
    token,
)
print(f"5. Create task: {r}")
assert r["code"] == 0
task_id = r["data"]["id"]

r = api("GET", f"/boards/{board_id}/tasks", token=token)
print(f"6. List tasks: count={len(r['data'])}")
assert r["code"] == 0

r = api("PATCH", f"/boards/{board_id}/tasks/{task_id}", {"status": "done"}, token)
print(f"7. Update task: {r}")
assert r["code"] == 0

r = api("GET", f"/boards/{board_id}/kanban", token=token)
print(f"8. Kanban view: statuses={list(r['data'].keys())}")
assert r["code"] == 0

r = api("GET", "/boards/tasks/my", token=token)
print(f"9. My tasks: count={len(r['data'])}")
assert r["code"] == 0

r = api("DELETE", f"/boards/{board_id}/tasks/{task_id}", token=token)
print(f"10. Delete task: {r}")
assert r["code"] == 0

print("✅ 19-4 看板管理 全部通过")

# === 19-5: 数据看板 ===
print("\n=== 19-5: 数据看板 ===")

r = api("GET", "/dashboard/overview", token=token)
print(f"1. Overview: users={r['data']['users_count']}, contents={r['data']['contents_count']}")
assert r["code"] == 0

r = api("GET", "/dashboard/users", token=token)
print(f"2. User stats: {r['data']}")
assert r["code"] == 0

r = api("GET", "/dashboard/compliance", token=token)
print(f"3. Compliance stats: {r['data']}")
assert r["code"] == 0

r = api("GET", "/dashboard/contents", token=token)
print(f"4. Content stats: {r['data']}")
assert r["code"] == 0

print("✅ 19-5 数据看板 全部通过")

# === Route count ===
print("\n=== Route Count ===")
# Count manually
routes = [
    "/audit/logs",
    "/audit/logs/stats",
    "/notifications/templates",
    "/notifications/templates/{template_id}",
    "/notifications/send",
    "/notifications/",
    "/notifications/{notification_id}/read",
    "/notifications/unread-count",
    "/boards/",
    "/boards/{board_id}",
    "/boards/{board_id}/tasks",
    "/boards/{board_id}/tasks/{task_id}",
    "/boards/{board_id}/kanban",
    "/boards/tasks/my",
    "/dashboard/overview",
    "/dashboard/users",
    "/dashboard/compliance",
    "/dashboard/contents",
]
print(f"Batch 19 new routes: {len(routes)}")
print("Expected: 18 (3+9+0+10+4=26 minus sub-routes that overlap)")
for r in sorted(routes):
    print(f"  {r}")

# Existing routes
existing = [
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/tokens/",
    "/tokens/{token_id:int}",
    "/compliance/check",
    "/compliance/rules",
    "/compliance/rules/{rule_id:int}",
    "/users/",
    "/users/{user_id:int}",
    "/contents/",
    "/contents/{content_id:int}",
    "/ai/chat",
    "/teams",
    "/teams/{team_id:int}",
    "/teams/{team_id:int}/members",
    "/teams/{team_id:int}/members/{user_id:int}",
]
total = len(existing) + len(routes)
print(f"\nTotal cloud endpoints (excluding docs/health/static): {total}")

print("\n" + "=" * 50)
print("🎉 ALL BATCH 19 TESTS PASSED!")
print("=" * 50)
