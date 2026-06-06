"""种子数据：Sage记忆评分引擎初始评分与演化日志。"""

import logging

from cloud.app.repositories.sage_repository import SageRepository
from cloud.app.research_database import get_research_db

logger = logging.getLogger(__name__)


def seed_sage_engine():
    db = get_research_db()
    try:
        repo = SageRepository(db)
        repo.init_tables()

        repo.upsert_score("episodic", 1, "brain_memory", 85.0, "hot", 15, "2026-06-03", 0.8, 0.9)
        repo.upsert_score("semantic", 1, "brain_memory", 65.0, "warm", 8, "2026-06-02", 0.7, 0.8)
        repo.upsert_score("procedural", 1, "brain_memory", 25.0, "cold", 2, "2026-05-20", 0.4, 0.5)
        repo.upsert_score("world_tree_node", 1, "world_tree", 90.0, "hot", 20, "2026-06-03", 0.9, 0.95)

        repo.log_evolution("manual", "score", None, None, '{"total_scored": 4, "tier_distribution": {"hot": 2, "warm": 1, "cold": 1}}')

        db.commit()
        logger.info("seed_sage_engine: 4 scores + 1 log created")
    finally:
        db.close()


if __name__ == "__main__":
    seed_sage_engine()
