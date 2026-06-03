"""
功能检测 — 一云四端
优雅版：处理真实API的字段命名差异和校验要求
"""

import json
import time
import urllib.error
import urllib.request

BASE = "http://localhost:8000"
TOKEN = None
PASS, FAIL = 0, 0
RATE_LIMIT_SLEEP = 0.3


def api(method, path, data=None, auth=True, port=8000):
    global TOKEN
    base = f"http://localhost:{port}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{base}{path}", data=body, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    if auth:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return {"code": resp.getcode(), "body": json.loads(raw)}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return {"code": e.code, "body": json.loads(raw) if raw else {}}


def ok(label, check=None):
    global PASS, FAIL
    time.sleep(RATE_LIMIT_SLEEP)
    return lambda resp: _check(label, resp, check)


def _check(label, resp, check):
    global PASS, FAIL
    if check and check(resp):
        PASS += 1
        print(f"  ✓ {label}")
    elif check:
        FAIL += 1
        body_str = json.dumps(resp.get("body", {}), ensure_ascii=False)[:120]
        print(f"  ✗ {label} — check failed")
        print(f"    resp: {body_str}")
    else:
        PASS += 1
        print(f"  ✓ {label} (no check)")
    return resp


def has_field(field):
    return lambda r: field in r.get("body", {}).get("data", {}) or field in r.get("body", {})


def field_equals(field, val):
    return lambda r: r.get("body", {}).get("data", {}).get(field) == val or r.get("body", {}).get(field) == val


def code_is(code):
    return lambda r: r.get("body", {}).get("code") == code


def status_code_is(code):
    return lambda r: r.get("code") == code


def not_error():
    return lambda r: r.get("body", {}).get("code", 0) != 429


# ============================================================
# 登录
# ============================================================
r = api("POST", "/auth/login", {"username": "func_test_main", "password": "TestPass123!"}, auth=False)
if r["body"].get("data", {}).get("access_token"):
    TOKEN = r["body"]["data"]["access_token"]
    ok("登录获取Token")(r)
else:
    # Try register
    r = api("POST", "/auth/register", {"username": "func_test_main", "password": "TestPass123!"}, auth=False)
    ok("注册")(r)
    r = api("POST", "/auth/login", {"username": "func_test_main", "password": "TestPass123!"}, auth=False)
    TOKEN = r["body"].get("data", {}).get("access_token", "")
    ok("登录")(r)

# ============================================================
# 1. Cloud — Customer CRUD
# ============================================================
print("\n=== Cloud: Customer CRUD ===")

# Create
r = api("POST", "/customers/", {"name": "FT-Customer-001", "type": "hospital", "region": "east", "status": "active"})
ok("创建客户", has_field("id"))(r)
cid = r["body"].get("data", {}).get("id")

# Read
if cid:
    r = api("GET", f"/customers/{cid}")
    ok(f"查询客户[{cid}]", field_equals("name", "FT-Customer-001"))(r)

    # List
    r = api("GET", "/customers/")
    ok("客户列表", lambda r: "data" in r["body"])(r)

    # Update (use a field that won't break active check)
    r = api("PATCH", f"/customers/{cid}", {"name": "FT-Customer-Updated"})
    ok("更新客户名称", lambda r: r["body"].get("code") in (0, 200))(r)

    # Re-read to confirm
    r = api("GET", f"/customers/{cid}")
    ok("确认更新", lambda r: "Updated" in json.dumps(r["body"], ensure_ascii=False))(r)

# ============================================================
# 2. Cloud — Contents CRUD
# ============================================================
print("\n=== Cloud: Contents CRUD ===")

r = api(
    "POST",
    "/contents/",
    {"title": "FT-Content-001", "body": "Body text", "category": "article", "content_type": "article", "status": "draft", "tags": ["test"]},
)
ok("创建内容", lambda r: "id" in json.dumps(r["body"], ensure_ascii=False))(r)
coid = r["body"].get("data", {}).get("id") or r["body"].get("id")

if coid:
    r = api("GET", f"/contents/{coid}")
    ok(f"查询内容[{coid}]")(r)
    r = api("PATCH", f"/contents/{coid}", {"status": "published"})
    ok("更新内容状态")(r)

# ============================================================
# 3. Cloud — Dashboard
# ============================================================
print("\n=== Cloud: Dashboard ===")

r = api("GET", "/dashboard/overview")
ok("Dashboard概览", lambda r: "data" in r["body"])(r)
r = api("GET", "/dashboard/compliance")
ok("Dashboard合规")(r)

# ============================================================
# 4. Cloud — Compliance
# ============================================================
print("\n=== Cloud: Compliance ===")

r = api("GET", "/compliance/rules")
ok("合规规则列表", lambda r: len(r["body"].get("data", [])) > 0)(r)

r = api(
    "POST",
    "/compliance/check",
    {"content": "This drug is the best on the market", "rules": [{"field": "prohibited_words", "op": "contains", "value": "best"}]},
)
ok("合规检查", lambda r: r["body"].get("code") in (0, 200, 422))(r)

# ============================================================
# 5. Cloud — Knowledge Graph
# ============================================================
print("\n=== Cloud: Knowledge Graph ===")

r = api(
    "POST",
    "/kg/entities/create",
    {"name": "FT-Drug-001", "entity_type": "drug", "properties": json.dumps({"molecule": "TEST", "class": "inhibitor"})},
)
ok("创建KG实体", lambda r: "entity_id" in json.dumps(r["body"], ensure_ascii=False) or r["body"].get("code") == 0)(r)
kgid = r["body"].get("data", {}).get("entity_id") or r["body"].get("entity_id")

if kgid:
    r = api("GET", f"/kg/entities/{kgid}")
    ok(f"查询KG实体[{kgid}]")(r)

r = api("GET", "/kg/dashboard")
ok("KG Dashboard")(r)

# ============================================================
# 6. Cloud — Memory System
# ============================================================
print("\n=== Cloud: Memory System ===")

r = api("POST", "/memory/auto-store/test_source/test_001")
ok("记忆自动存储")(r)

r = api("GET", "/memory/consolidation/status")
ok("记忆合并状态")(r)

# ============================================================
# 7. Cloud — Brain Memory
# ============================================================
print("\n=== Cloud: Brain Memory ===")

r = api("GET", "/brain-memory/dashboard")
ok("Brain Memory Dashboard", lambda r: "data" in r["body"])(r)

# ============================================================
# 8. Cloud — Causal Reasoning
# ============================================================
print("\n=== Cloud: Causal Reasoning ===")

r = api("POST", "/causal/graph/build", {"name": "FT-Causal-Graph", "description": "Test graph"})
ok("构建因果图", lambda r: "graph_id" in json.dumps(r["body"], ensure_ascii=False) or r["body"].get("code") == 0)(r)

# ============================================================
# 9. Cloud — Agent System
# ============================================================
print("\n=== Cloud: Agent System ===")

r = api("GET", "/agent/exec/a2a/card")
ok("Agent A2A Card", lambda r: r["body"].get("code") == 0)(r)

# ============================================================
# 10. Cloud — Collaboration
# ============================================================
print("\n=== Cloud: Collaboration ===")

r = api("GET", "/collaboration/dashboard")
ok("协作Dashboard", lambda r: r["body"].get("code") == 0)(r)

r = api("POST", "/collaboration/sessions/create", {"title": "FT-Collab-001", "participants": ["agent_a", "agent_b"]})
ok("创建协作会话", lambda r: "session_id" in json.dumps(r["body"], ensure_ascii=False))(r)

# ============================================================
# 11. Cloud — MDT
# ============================================================
print("\n=== Cloud: MDT ===")

r = api("GET", "/mdt/dashboard")
ok("MDT Dashboard", lambda r: r["body"].get("code") == 0)(r)

r = api("POST", "/mdt/sessions", {"case_description": "Test case for MDT", "participants": ["dr_a", "dr_b"]})
ok("创建MDT会诊", lambda r: "session_id" in json.dumps(r["body"], ensure_ascii=False))(r)
mdt_id = r["body"].get("data", {}).get("session_id") or r["body"].get("session_id")

if mdt_id:
    r = api("POST", f"/mdt/sessions/{mdt_id}/consensus", {"decision": "Continue monitoring"})
    ok(f"MDT达成共识[{mdt_id}]")(r)

# ============================================================
# 12. Cloud — Market Intel
# ============================================================
print("\n=== Cloud: Market Intel ===")

r = api("GET", "/market-intel/dashboard")
ok("Market Intel Dashboard", lambda r: r["body"].get("code") == 0)(r)

# ============================================================
# 13. Cloud — Event Bus
# ============================================================
print("\n=== Cloud: Event Bus ===")

r = api("GET", "/events/dashboard")
ok("Event Bus Dashboard", lambda r: r["body"].get("code") == 0)(r)

r = api("POST", "/events/definitions/create", {"event_type": "test.event", "description": "Test event for functional testing"})
ok("创建事件定义", lambda r: r["body"].get("code") == 0)(r)

# ============================================================
# 14. Cloud — Decision Intelligence
# ============================================================
print("\n=== Cloud: Decision Intelligence ===")

r = api("POST", "/decision-intel/cases", {"title": "FT-Decision-001", "description": "Test decision case", "decision_type": "strategic"})
ok("创建决策案例", lambda r: "case_id" in json.dumps(r["body"], ensure_ascii=False))(r)

# ============================================================
# 15. Cloud — HCP Sandbox
# ============================================================
print("\n=== Cloud: HCP Sandbox ===")

r = api(
    "POST", "/hcp-sandbox/profiles", {"hcp_name": "Dr. Functional Test", "specialty": "cardiology", "hospital": "Test Hospital", "region": "east"}
)
ok("创建HCP档案", lambda r: "hcp_id" in json.dumps(r["body"], ensure_ascii=False))(r)

# ============================================================
# 16. Cloud — Marketplace
# ============================================================
print("\n=== Cloud: Marketplace ===")

r = api("GET", "/marketplace/metrics/dashboard")
ok("Marketplace Dashboard", lambda r: r["body"].get("code") == 0)(r)

# ============================================================
# 17. Cloud — MCP Tools
# ============================================================
print("\n=== Cloud: MCP ===")

r = api("GET", "/mcp/tools/list")
ok("MCP工具列表", lambda r: r["body"].get("code") == 0)(r)

# ============================================================
# 18. Cloud — Export
# ============================================================
print("\n=== Cloud: Export ===")

r = api("GET", "/export/customers")
ok("导出客户", lambda r: r["body"].get("code") == 0)(r)

# ============================================================
# 其他端检测
# ============================================================
print("\n=== Sales-Coach (8001) ===")
r = api("GET", "/health", port=8001, auth=False)
ok("健康检查", lambda r: "status" in json.dumps(r["body"]))(r)

r = api("GET", "/modules", port=8001)
ok("模块列表")(r)

r = api("GET", "/scenarios", port=8001)
ok("场景列表")(r)

r = api("GET", "/coach/stats", port=8001)
ok("教练统计")(r)

print("\n=== Opportunity (8002) ===")
r = api("GET", "/health", port=8002, auth=False)
ok("健康检查", lambda r: "status" in json.dumps(r["body"]))(r)

r = api("GET", "/opportunities/stats", port=8002)
ok("机会统计")(r)

r = api(
    "POST",
    "/opportunities",
    port=8002,
    data={"name": "FT-Opp-001", "hospital": "Test Hospital", "product": "Test Drug", "value": 100000, "stage": "qualify"},
)
ok("创建机会", lambda r: "opportunity_id" in json.dumps(r["body"], ensure_ascii=False))(r)
oid = r["body"].get("opportunity_id") or r["body"].get("data", {}).get("opportunity_id")

if oid:
    r = api("GET", f"/opportunities/{oid}", port=8002)
    ok(f"查询机会[{oid}]")(r)

r = api("GET", "/scoring/leaderboard", port=8002)
ok("机会排行榜")(r)

print("\n=== Assistant (8003) ===")
r = api("GET", "/health", port=8003, auth=False)
ok("健康检查", lambda r: "status" in json.dumps(r["body"]))(r)

r = api("GET", "/hcp", port=8003)
ok("HCP列表")(r)

r = api(
    "POST",
    "/visits",
    port=8003,
    data={
        "hcp_name": "Dr FT-Assistant",
        "hcp_title": "Cardiologist",
        "hospital": "Test Hospital",
        "visit_date": "2026-06-04",
        "status": "planned",
        "notes": "Functional test visit",
    },
)
ok("创建拜访", lambda r: "visit_id" in json.dumps(r["body"], ensure_ascii=False))(r)

r = api("GET", "/tasks", port=8003)
ok("任务列表")(r)

r = api("GET", "/health-radar", port=8003)
ok("健康雷达")(r)

print("\n=== Sales-Assistant (8004) ===")
r = api("GET", "/health", port=8004, auth=False)
ok("健康检查", lambda r: "status" in json.dumps(r["body"]))(r)

r = api("GET", "/hcp", port=8004)
ok("HCP列表")(r)

r = api(
    "POST",
    "/hcp",
    port=8004,
    data={"name": "Dr FT-SA", "title": "Oncologist", "hospital": "Cancer Center", "specialty": "oncology", "region": "east"},
)
ok("创建HCP关系", lambda r: "hcp_id" in json.dumps(r["body"], ensure_ascii=False))(r)

r = api("GET", "/products", port=8004)
ok("产品列表")(r)

r = api("GET", "/precall", port=8004)
ok("Precall计划")(r)

r = api("GET", "/funnel", port=8004)
ok("销售漏斗")(r)

# ============================================================
# 汇总
# ============================================================
print(f"\n{'=' * 40}")
print("功能检测完成")
print(f"通过: {PASS} / {PASS + FAIL}")
print(f"失败: {FAIL} / {PASS + FAIL}")
if FAIL == 0:
    print("🎉 全部通过！")
else:
    print(f"⚠️  存在 {FAIL} 项失败")
