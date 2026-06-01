import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/cloud.db")


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite://")


def get_db_type() -> str:
    return "sqlite" if is_sqlite() else "postgresql"


class PGRow(dict):
    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return list(self.values())[key]
        return dict.__getitem__(self, key)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class PGCompatCursor:
    def __init__(self, cur, description=None):
        self._cur = cur
        self._desc = description
        self.lastrowid = None

    def execute(self, sql, params=None):
        sql = sql.replace("?", "%s")
        self._cur.execute(sql, params)
        self._desc = self._cur.description
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        if self._desc is None:
            return PGRow(row) if isinstance(row, dict) else row
        cols = [d[0] for d in self._desc] if self._desc else []
        if isinstance(row, (list, tuple)):
            return PGRow(zip(cols, row))
        return PGRow(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        if not rows:
            return []
        if self._desc is None:
            result = []
            for row in rows:
                if isinstance(row, dict):
                    result.append(PGRow(row))
                else:
                    result.append(row)
            return result
        cols = [d[0] for d in self._desc] if self._desc else []
        result = []
        for row in rows:
            if isinstance(row, (list, tuple)):
                result.append(PGRow(zip(cols, row)))
            else:
                result.append(PGRow(row))
        return result

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        self._cur.close()


class PGCompatConnection:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        pgc = PGCompatCursor(cur)
        pgc.execute(sql, params)
        return pgc

    def commit(self):
        self._conn.commit()

    def cursor(self):
        return self._conn.cursor()

    def close(self):
        self._conn.close()
