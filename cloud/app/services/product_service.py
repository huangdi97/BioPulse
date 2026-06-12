"""产品服务，负责产品搜索与创建。"""

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories.product_repository import ProductRepository
from shared.base_service import BaseService


class ProductService(BaseService):
    """产品服务，提供产品搜索与创建功能。"""

    def search(self, q: str = "", category: str = "") -> list:
        repo = ProductRepository(self._connection())
        return repo.search(q=q, category=category)

    def get_by_id(self, product_id: int) -> dict:
        repo = ProductRepository(self._connection())
        product = repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def create(
        self,
        name: str,
        category: str = "",
        brand: str = "",
        model: str = "",
        spec: str = "",
        unit_price: float = 0.0,
        keywords: list | None = None,
        tech_params: dict | None = None,
        cert_status: str = "",
    ) -> dict:
        repo = ProductRepository(self._connection())
        product_id = repo.create(
            name=name,
            category=category,
            brand=brand,
            model=model,
            spec=spec,
            unit_price=unit_price,
            keywords=keywords,
            tech_params=tech_params,
            cert_status=cert_status,
        )
        return repo.get_by_id(product_id)
