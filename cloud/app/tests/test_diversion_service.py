from cloud.app.services.diversion_service import DiversionService


class TestDiversionService:
    def test_diversion_detect_cross_region(self):
        svc = DiversionService()
        data = [
            {"product": "药A", "region": "beijing", "authorized_region": "shanghai", "quantity": 60},
        ]
        anomalies = svc.check_distribution(data)
        assert len(anomalies) == 1
        assert anomalies[0]["pattern"] == "cross_region"
        assert anomalies[0]["region"] == "beijing"
        assert anomalies[0]["severity"] == "medium"

    def test_diversion_detect_stuffing(self):
        svc = DiversionService()
        data = [
            {"product": "药B", "region": "shanghai", "authorized_region": "shanghai", "sell_in": 70, "sell_out": 60, "timestamp": "2024-01-01"},
            {"product": "药B", "region": "shanghai", "authorized_region": "shanghai", "sell_in": 80, "sell_out": 60, "timestamp": "2024-01-02"},
            {"product": "药B", "region": "shanghai", "authorized_region": "shanghai", "sell_in": 100, "sell_out": 50, "timestamp": "2024-01-03"},
        ]
        anomalies = svc.check_distribution(data)
        assert len(anomalies) == 1
        assert anomalies[0]["pattern"] == "stuffing"
        assert anomalies[0]["region"] == "shanghai"
        assert anomalies[0]["severity"] == "high"

    def test_diversion_anomaly_fluctuation(self):
        svc = DiversionService()
        data = [
            {"product": "药C", "region": "guangzhou", "quantity": 100},
            {"product": "药C", "region": "guangzhou", "quantity": 100},
            {"product": "药C", "region": "guangzhou", "quantity": 100},
            {"product": "药C", "region": "guangzhou", "quantity": 1000},
        ]
        anomalies = svc.check_distribution(data)
        assert len(anomalies) == 1
        assert anomalies[0]["pattern"] == "fluctuation"
        assert anomalies[0]["region"] == "guangzhou"
        assert anomalies[0]["severity"] == "medium"

    def test_diversion_ignore_normal(self):
        svc = DiversionService()
        data = [
            {"product": "药D", "region": "beijing", "authorized_region": "beijing", "quantity": 50},
        ]
        anomalies = svc.check_distribution(data)
        assert len(anomalies) == 0
