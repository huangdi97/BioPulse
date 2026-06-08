"""HCP 产品/关系辅助 mixin。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import HcpRepository, ProductRepository, RelationRepository


class HcpStatsMixin:
    def create_product(self, body, user_id: int) -> int:
        """创建产品档案。

        Args:
            body: 产品创建请求体。
            user_id: 创建人用户ID。

        Returns:
            新产品记录ID。

        Raises:
            sqlite3.Error: 当产品写入失败时由仓储层抛出。
        """
        repo = ProductRepository(self.db)
        now = self._now()
        return repo.create(body.model_dump(), extra={"created_by": user_id, "created_at": now, "updated_at": now})

    def list_products(self, page: int, page_size: int, category: Optional[str] = None, company: Optional[str] = None) -> tuple:
        """分页查询活跃产品档案。

        Args:
            page: 当前页码。
            page_size: 每页数量。
            category: 可选的产品分类过滤关键词。
            company: 可选的公司过滤关键词。

        Returns:
            仓储层分页元组。

        Raises:
            sqlite3.Error: 当产品查询失败时由仓储层抛出。
        """
        repo = ProductRepository(self.db)
        conditions, params = ["is_active = 1"], []
        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        if company:
            conditions.append("company LIKE ?")
            params.append(f"%{company}%")
        return repo.paginate(page, page_size, conditions, params)

    def get_product(self, product_id: int) -> dict:
        """读取单个产品档案。

        Args:
            product_id: 产品记录ID。

        Returns:
            产品记录字典。

        Raises:
            HTTPException: 当产品不存在或已停用时抛出404。
        """
        repo = ProductRepository(self.db)
        row = repo.get_by_id(product_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return dict(row)

    def update_product(self, product_id: int, body) -> dict:
        """更新产品档案字段。

        Args:
            product_id: 产品记录ID。
            body: 产品更新请求体。

        Returns:
            更新后的产品记录字典；无更新字段时返回原记录。

        Raises:
            HTTPException: 当产品不存在或已停用时抛出404。
        """
        repo = ProductRepository(self.db)
        row = repo.get_by_id(product_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = self._now()
        repo.update(product_id, updates)
        return dict(repo.get_by_id(product_id))

    def delete_product(self, product_id: int) -> None:
        """软删除产品档案。

        Args:
            product_id: 产品记录ID。

        Returns:
            None。

        Raises:
            HTTPException: 当产品不存在或已停用时抛出404。
        """
        repo = ProductRepository(self.db)
        row = repo.get_by_id(product_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        repo.soft_delete(product_id)

    def create_relation(self, hcp_id: int, body, user_id: int) -> int:
        """创建HCP与产品之间的关联关系。

        Args:
            hcp_id: HCP记录ID。
            body: 关联关系创建请求体。
            user_id: 创建人用户ID。

        Returns:
            新关联关系ID。

        Raises:
            HTTPException: 当HCP或产品不存在、已停用时抛出404。
        """
        hcp_repo = HcpRepository(self.db)
        product_repo = ProductRepository(self.db)
        relation_repo = RelationRepository(self.db)
        hcp_row = hcp_repo.get_by_id(hcp_id)
        if not hcp_row or not hcp_row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        prod_row = product_repo.get_by_id(body.product_id)
        if not prod_row or not prod_row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        now = self._now()
        return relation_repo.create(
            {"hcp_id": hcp_id, "product_id": body.product_id, "relation_type": body.relation_type, "strength": body.strength, "notes": body.notes},
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )

    def list_relations(self, hcp_id: int) -> list:
        """列出指定HCP的活跃产品关联。

        Args:
            hcp_id: HCP记录ID。

        Returns:
            带产品名称的关联关系列表。

        Raises:
            HTTPException: 当HCP不存在或已停用时抛出404。
        """
        hcp_repo = HcpRepository(self.db)
        hcp_row = hcp_repo.get_by_id(hcp_id)
        if not hcp_row or not hcp_row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        rows = self.db.execute(
            "SELECT r.id, r.hcp_id, r.product_id, r.relation_type, r.strength, "
            "r.notes, r.is_active, p.name AS product_name "
            "FROM hcp_product_relation r JOIN product p ON r.product_id = p.id "
            "WHERE r.hcp_id = ? AND r.is_active = 1 AND p.is_active = 1",
            (hcp_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_relation(self, relation_id: int) -> None:
        """软删除HCP产品关联关系。

        Args:
            relation_id: 关联关系ID。

        Returns:
            None。

        Raises:
            HTTPException: 当关联关系不存在或已停用时抛出404。
        """
        repo = RelationRepository(self.db)
        row = repo.get_by_id(relation_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
        repo.soft_delete(relation_id)
