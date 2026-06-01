from cloud.app.database import get_db
from cloud.app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, db=None):
        self.db = db or next(get_db())
        self.repo = ProductRepository(self.db)

    def search_products(self, q: str = "", category: str = "") -> list[dict]:
        return self.repo.search(q=q, category=category)
