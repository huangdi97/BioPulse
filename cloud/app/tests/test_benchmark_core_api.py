import sqlite3

import pytest

from cloud.app.database import DB_PATH
from cloud.app.repositories import PiRepository, ProductRepository
from cloud.app.services.compliance_enforcer import ComplianceEnforcer


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class TestCoreAPIPerformance:
    def test_pi_search(self, benchmark):
        db = _get_db()
        try:
            repo = PiRepository(db)
            result = benchmark(repo.search, "test")
            assert isinstance(result, list)
        finally:
            db.close()

    def test_product_search(self, benchmark):
        db = _get_db()
        try:
            repo = ProductRepository(db)
            result = benchmark(repo.search, "FBS")
            assert isinstance(result, list)
        finally:
            db.close()

    def test_compliance_enforce(self, benchmark):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        enforcer = ComplianceEnforcer(db)
        visit = {"notes": "正常拜访", "expenses": 0}
        result = benchmark(enforcer.check_visit, visit)
        assert isinstance(result, list)

    def test_langgraph_execution(self, benchmark):
        try:
            from cloud.langgraph.graph import get_test_graph
        except ImportError:
            pytest.skip("langgraph not installed")

        graph = get_test_graph()
        result = benchmark(
            graph.invoke,
            {
                "messages": ["hello"],
                "next_agent": "",
                "metadata": {},
                "needs_review": False,
            },
            {"configurable": {"thread_id": "bench-test"}},
        )
        assert "processed_by_B" in result["messages"]

    def test_product_matching(self, benchmark):
        from cloud.app.services.product_matching_service import _tokenize

        result = benchmark(_tokenize, "PCR amplification for DNA sequencing")
        assert isinstance(result, set)

    def test_dashboard_overview(self, benchmark):
        from cloud.app.services.dashboard_service import DashboardService

        db = _get_db()
        try:
            service = DashboardService(db)
            result = benchmark(service.get_overview)
            assert isinstance(result, dict)
        finally:
            db.close()

    def test_auth_login(self, benchmark):
        from shared.auth import hash_password, verify_password

        hashed = hash_password("test_password_123")
        result = benchmark(verify_password, "test_password_123", hashed)
        assert result is True

    def test_compliance_engine(self, benchmark):
        from shared.compliance import check_content

        rules = [
            {"category": "prohibited_word", "keyword": "cure"},
            {"category": "prohibited_word", "keyword": "guarantee"},
            {"category": "mandatory_claim", "keyword": "consult your doctor"},
            {"category": "dosage_limit", "keyword": "dosage", "max_value": "100"},
            {"category": "comparative_claim", "keyword": ""},
        ]
        content = "This product helps with symptom relief. Please consult your doctor before use. Take 50mg daily."
        result = benchmark(check_content, content, rules)
        assert result.passed is True
        assert result.score == 1.0

    def test_research_pi_query(self, benchmark):
        from cloud.app.services.research_pi_service import ResearchPiService

        service = ResearchPiService()
        result = benchmark(service.search, "test")
        assert isinstance(result, list)
