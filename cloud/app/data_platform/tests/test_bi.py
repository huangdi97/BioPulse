from cloud.app.data_platform.analytics.bi_view import BIViewService

SAMPLE_ROWS = [
    {
        "activity_date": "2026-06-01",
        "team_id": "team-east",
        "visit_count": 3,
        "engagement_score": 85.0,
        "opportunity_amount": 5000.0,
    },
    {
        "activity_date": "2026-06-01",
        "team_id": "team-east",
        "visit_count": 1,
        "engagement_score": 70.0,
        "opportunity_amount": 3000.0,
    },
    {
        "activity_date": "2026-06-02",
        "team_id": "team-west",
        "visit_count": 5,
        "engagement_score": 92.0,
        "opportunity_amount": 8000.0,
    },
]


class TestBIViewService:
    def test_report_data_structure(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data()
        assert "filters" in report
        assert "rows" in report
        assert "totals" in report
        assert "chart" in report

    def test_report_data_row_aggregation(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data()
        rows = report["rows"]
        east_rows = [r for r in rows if r["team_id"] == "team-east"]
        assert len(east_rows) == 1
        assert east_rows[0]["visit_count"] == 4

    def test_report_data_filter_by_team(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data(team_id="team-west")
        assert report["filters"]["team_id"] == "team-west"
        assert len(report["rows"]) == 1
        assert report["rows"][0]["team_id"] == "team-west"

    def test_report_data_date_range(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data(date_from="2026-06-02", date_to="2026-06-02")
        assert report["filters"]["date_from"] == "2026-06-02"
        assert report["filters"]["date_to"] == "2026-06-02"
        assert len(report["rows"]) == 1

    def test_report_data_custom_metrics(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data(metrics=["visit_count"])
        assert report["filters"]["metrics"] == ["visit_count"]
        assert "opportunity_amount" not in report["totals"]

    def test_report_data_custom_group_by(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data(group_by=["activity_date"])
        assert report["filters"]["group_by"] == ["activity_date"]
        assert len(report["rows"]) == 2

    def test_totals_computation(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data()
        totals = report["totals"]
        assert totals["visit_count"] == 9
        assert totals["opportunity_amount"] == 16000.0

    def test_chart_structure(self):
        service = BIViewService(rows=SAMPLE_ROWS)
        report = service.report_data()
        chart = report["chart"]
        assert "labels" in chart
        assert "series" in chart
        assert len(chart["labels"]) == len(report["rows"])
        assert len(chart["series"]) == 3
        for serie in chart["series"]:
            assert "name" in serie
            assert "data" in serie

    def test_empty_rows(self):
        service = BIViewService(rows=[])
        report = service.report_data()
        assert report["rows"] == []
        assert report["totals"]["visit_count"] == 0
        assert report["totals"]["opportunity_amount"] == 0
        assert report["chart"]["labels"] == []
        for serie in report["chart"]["series"]:
            assert serie["data"] == []
