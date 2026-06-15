from cloud.app.services.admission_service import AdmissionService


class TestAdmissionService:
    def test_create_admission(self):
        svc = AdmissionService()
        result = svc.create({"hospital_name": "test"})
        assert isinstance(result, dict)
