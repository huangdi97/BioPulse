"""SAGE自进化记忆评分与演化日志数据访问层。"""

from cloud.app.research_database import get_research_db


class SageRepository:
    """SAGE仓库，管理记忆评分、分层、演化日志等数据。"""

    def __init__(self, db=None):
        self.db = db or get_research_db()

    def init_tables(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sage_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                component TEXT NOT NULL,
                score REAL NOT NULL DEFAULT 0.0,
                tier TEXT NOT NULL DEFAULT 'cold',
                access_count INTEGER DEFAULT 0,
                last_access TEXT,
                utility_score REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.5,
                last_scored_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_type, memory_id)
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sage_evolution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                triggered_by TEXT NOT NULL,
                action TEXT NOT NULL,
                memory_type TEXT,
                memory_id INTEGER,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def upsert_score(self, memory_type, memory_id, component, score, tier, access_count=0, last_access=None, utility_score=0.5, confidence=0.5):
        self.db.execute(
            """
            INSERT INTO sage_scores
                (memory_type, memory_id, component, score, tier,
                 access_count, last_access, utility_score, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(memory_type, memory_id) DO UPDATE SET
                component=excluded.component,
                score=excluded.score,
                tier=excluded.tier,
                access_count=excluded.access_count,
                last_access=excluded.last_access,
                utility_score=excluded.utility_score,
                confidence=excluded.confidence,
                last_scored_at=CURRENT_TIMESTAMP
        """,
            (memory_type, memory_id, component, score, tier, access_count, last_access, utility_score, confidence),
        )
        self.db.commit()
        row = self.db.execute(
            "SELECT id FROM sage_scores WHERE memory_type=? AND memory_id=?",
            (memory_type, memory_id),
        ).fetchone()
        return row["id"] if row else 0

    def get_all_scores(self):
        rows = self.db.execute("SELECT * FROM sage_scores ORDER BY score DESC").fetchall()
        return [dict(r) for r in rows]

    def get_scores_by_tier(self, tier):
        rows = self.db.execute(
            "SELECT * FROM sage_scores WHERE tier=? ORDER BY score DESC",
            (tier,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_score(self, memory_type, memory_id):
        row = self.db.execute(
            "SELECT * FROM sage_scores WHERE memory_type=? AND memory_id=?",
            (memory_type, memory_id),
        ).fetchone()
        return dict(row) if row else None

    def delete_score(self, memory_type, memory_id):
        cur = self.db.execute(
            "DELETE FROM sage_scores WHERE memory_type=? AND memory_id=?",
            (memory_type, memory_id),
        )
        self.db.commit()
        return cur.rowcount > 0

    def log_evolution(self, triggered_by, action, memory_type=None, memory_id=None, result=None):
        cur = self.db.execute(
            "INSERT INTO sage_evolution_log (triggered_by, action, memory_type, memory_id, result) VALUES (?, ?, ?, ?, ?)",
            (triggered_by, action, memory_type, memory_id, result),
        )
        self.db.commit()
        return cur.lastrowid

    def get_recent_logs(self, limit=50):
        rows = self.db.execute(
            "SELECT * FROM sage_evolution_log ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
