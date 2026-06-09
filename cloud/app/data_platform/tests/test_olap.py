from cloud.app.data_platform.analytics.olap_service import OLAPService

SAMPLE_ROWS = [
    {
        "activity_date": "2026-06-01",
        "team_id": "team-east",
        "customer_id": "hcp-001",
        "product_id": "prod-001",
        "visit_count": 3,
        "engagement_score": 85.0,
        "opportunity_amount": 5000.0,
        "compliance_issue_count": 0,
    },
    {
        "activity_date": "2026-06-01",
        "team_id": "team-east",
        "customer_id": "hcp-002",
        "product_id": "prod-002",
        "visit_count": 1,
        "engagement_score": 70.0,
        "opportunity_amount": 3000.0,
        "compliance_issue_count": 2,
    },
    {
        "activity_date": "2026-06-02",
        "team_id": "team-west",
        "customer_id": "hcp-003",
        "product_id": "prod-001",
        "visit_count": 5,
        "engagement_score": 92.0,
        "opportunity_amount": 8000.0,
        "compliance_issue_count": 1,
    },
    {
        "activity_date": "2026-06-02",
        "team_id": "team-west",
        "customer_id": "hcp-004",
        "product_id": "prod-003",
        "visit_count": 2,
        "engagement_score": 60.0,
        "opportunity_amount": 2000.0,
        "compliance_issue_count": 0,
    },
]


class TestOLAPService:
    def test_query_default_dimensions_and_metrics(self):
        service = OLAPService(rows=SAMPLE_ROWS)
        results = service.query()
        assert len(results) == 2
        dates = [r["activity_date"] for r in results]
        assert "2026-06-01" in dates
        assert "2026-06-02" in dates

    def test_query_sum_visit_count_by_team(self):
        service = OLAPService(rows=SAMPLE_ROWS)
        results = service.query(
            dimensions=["team_id"],
            metrics={"visit_count": "sum"},
        )
        assert len(results) == 2
        east = next(r for r in results if r["team_id"] == "team-east")
        west = next(r for r in results if r["team_id"] == "team-west")
        assert east["visit_count"] == 4
        assert west["visit_count"] == 7

    def test_query_avg_engagement_score_by_product(self):
        service = OLAPService(rows=SAMPLE_ROWS)
        results = service.query(
            dimensions=["product_id"],
            metrics={"engagement_score": "avg"},
        )
        prod_001 = next(r for r in results if r["product_id"] == "prod-001")
        assert prod_001["engagement_score"] == round((85.0 + 92.0) / 2, 4)

    def test_query_with_filters(self):
        service = OLAPService(rows=SAMPLE_ROWS)
        results = service.query(
            dimensions=["team_id"],
            filters={"team_id": "team-east"},
            metrics={"visit_count": "sum"},
        )
        assert len(results) == 1
        assert results[0]["team_id"] == "team-east"

    def test_query_date_range(self):
        service = OLAPService(rows=SAMPLE_ROWS)
        results = service.query(
            dimensions=["activity_date"],
            date_from="2026-06-02",
        )
        assert len(results) == 1
        assert results[0]["activity_date"] == "2026-06-02"

    def test_query_limit(self):
        service = OLAPService(rows=SAMPLE_ROWS)
        results = service.query(
            dimensions=["activity_date", "team_id"],
            limit=1,
        )
        assert len(results) <= 1

    def test_aggregate_sum(self):
        result = OLAPService._aggregate([{"val": 10}, {"val": 20}, {"val": 30}], "val", "sum")
        assert result == 60

    def test_aggregate_avg(self):
        result = OLAPService._aggregate([{"val": 10}, {"val": 20}, {"val": 30}], "val", "avg")
        assert result == round(60 / 3, 4)

    def test_aggregate_min_max(self):
        rows = [{"val": 10}, {"val": 20}, {"val": 5}]
        assert OLAPService._aggregate(rows, "val", "min") == 5
        assert OLAPService._aggregate(rows, "val", "max") == 20

    def test_aggregate_count(self):
        rows = [{"val": 10}, {"val": 20}]
        assert OLAPService._aggregate(rows, "val", "count") == 2

    def test_aggregate_empty(self):
        assert OLAPService._aggregate([], "val", "sum") == 0
        assert OLAPService._aggregate([], "val", "avg") == 0

    def test_build_sql(self):
        service = OLAPService()
        sql = service.build_sql(
            fact_table="fact_business_activity_daily",
            dimensions=["team_id", "activity_date"],
            metrics={"visit_count": "sum", "engagement_score": "avg"},
            filters={"team_id": "team-east"},
        )
        assert "fact_business_activity_daily" in sql
        assert "SUM(visit_count)" in sql
        assert "AVG(engagement_score)" in sql
        assert "GROUP BY team_id, activity_date" in sql
        assert "WHERE team_id = :team_id" in sql

    def test_build_sql_no_filters(self):
        service = OLAPService()
        sql = service.build_sql(
            fact_table="my_fact",
            dimensions=["product_id"],
            metrics={"visit_count": "sum"},
        )
        assert "WHERE" not in sql

    def test_filter_rows_handles_missing_date_column(self):
        service = OLAPService(rows=[{"date": "2026-06-01", "other": "a"}])
        rows = service._filter_rows({}, "2026-06-01", "2026-06-01")
        assert len(rows) == 1

    def test_init_without_rows(self):
        service = OLAPService()
        assert service.rows == []
