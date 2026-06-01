from cloud.app.repositories import AuditLogsRepository, CustomersRepository
from cloud.app.services.base import BaseService
from shared.csv_export import export_csv


class ExportService(BaseService):
    def export_audit_logs(self) -> dict:
        items = AuditLogsRepository(self.db).get_all()
        columns = [
            "id",
            "user_id",
            "action",
            "entity_type",
            "entity_id",
            "detail",
            "source_end",
            "ip_address",
            "created_at",
        ]
        file_path = export_csv(items, columns, "audit_logs")
        return {"file_path": file_path, "row_count": len(items)}

    def export_customers(self) -> dict:
        items = CustomersRepository(self.db).get_all()
        columns = [
            "id",
            "name",
            "title",
            "hospital",
            "department",
            "specialty",
            "phone",
            "email",
            "tags",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]
        file_path = export_csv(items, columns, "customers")
        return {"file_path": file_path, "row_count": len(items)}
