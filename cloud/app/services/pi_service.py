from cloud.app.database import get_db
from cloud.app.repositories.pi_repository import PiRepository


class PiService:
    def __init__(self, db=None):
        self.db = db or next(get_db())
        self.repo = PiRepository(self.db)

    def get_or_create_pi(self, name: str, institution: str,
                         department: str = "", title: str = "",
                         hcp_id: int | None = None) -> dict:
        existing = self.repo.search(name)
        for pi in existing:
            if pi["name"] == name and pi["institution"] == institution:
                return pi
        pi_id = self.repo.create(name=name, institution=institution,
                                 department=department, title=title, hcp_id=hcp_id)
        return self.repo.get_by_id(pi_id)

    def update_papers(self, pi_id: int, papers: list[dict]) -> dict | None:
        pi = self.repo.get_by_id(pi_id)
        if not pi:
            return None
        total = len(papers)
        h_index = 0
        citations = sorted((p.get("cited_by", []) for p in papers), key=len, reverse=True)
        for i, c in enumerate(citations, 1):
            if len(c) >= i:
                h_index = i
        self.repo.update(pi_id, total_papers=total, h_index=h_index)
        return self.repo.get_by_id(pi_id)

    def search_pis(self, keyword: str) -> list[dict]:
        return self.repo.search(keyword)
