import pytest
import sqlite3
import os
from cloud.app.services.compliance_enforcer import ComplianceEnforcer
from cloud.app.repositories import PiRepository, ProductRepository
from cloud.app.database import DB_PATH


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
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        enforcer = ComplianceEnforcer(db)
        visit = {"notes": "正常拜访", "expenses": 0}
        result = benchmark(enforcer.check_visit, visit)
        assert isinstance(result, list)

    def test_langgraph_execution(self, benchmark):
        from cloud.langgraph.graph import get_test_graph
        graph = get_test_graph()
        result = benchmark(
            graph.invoke,
            {'messages': ['hello'], 'next_agent': '', 'metadata': {}, 'needs_review': False},
            {'configurable': {'thread_id': 'bench-test'}}
        )
        assert "processed_by_B" in result["messages"]

    def test_product_matching(self, benchmark):
        from cloud.app.services.product_matching_service import _tokenize
        result = benchmark(_tokenize, "PCR amplification for DNA sequencing")
        assert isinstance(result, set)
