import re
from typing import Any

TYPE_MAP = {
    "INTEGER": "Integer",
    "INT": "Integer",
    "REAL": "Float",
    "FLOAT": "Float",
    "TEXT": "Text",
    "BLOB": "LargeBinary",
    "BOOLEAN": "Integer",
    "TIMESTAMP": "Text",
}


def _split_top_level_commas(text: str) -> list[str]:
    parts = []
    depth = 0
    current: list[str] = []
    for ch in text:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def _parse_default_value(tokens: list[str], start: int) -> tuple[str | None, int]:
    if start >= len(tokens):
        return None, 0
    token = tokens[start]
    if token.startswith("'") or token.startswith('"'):
        quote_char = token[0]
        if len(token) > 1 and token.endswith(quote_char) and not token.endswith("\\" + quote_char):
            return token, 1
        parts = [token]
        for j in range(start + 1, len(tokens)):
            parts.append(tokens[j])
            if tokens[j].endswith(quote_char) and not tokens[j].endswith("\\" + quote_char):
                break
        return " ".join(parts), len(parts)
    if token.upper() == "CURRENT_TIMESTAMP":
        return "CURRENT_TIMESTAMP", 1
    if re.match(r"^-?\d+(\.\d+)?$", token):
        return token, 1
    if token.upper() == "NULL":
        return "NULL", 1
    return token, 1


def _parse_constraints(tokens: list[str]) -> dict[str, Any]:
    constraints: dict[str, Any] = {
        "nullable": True,
        "primary_key": False,
        "autoincrement": False,
        "unique": False,
        "default": None,
        "foreign_key": None,
    }
    i = 0
    while i < len(tokens):
        token = tokens[i].upper()
        if token == "NOT" and i + 1 < len(tokens) and tokens[i + 1].upper() == "NULL":
            constraints["nullable"] = False
            i += 2
        elif token == "PRIMARY" and i + 1 < len(tokens) and tokens[i + 1].upper() == "KEY":
            constraints["primary_key"] = True
            i += 2
        elif token == "AUTOINCREMENT":
            constraints["autoincrement"] = True
            i += 1
        elif token == "UNIQUE":
            constraints["unique"] = True
            i += 1
        elif token == "REFERENCES" and i + 1 < len(tokens):
            ref = tokens[i + 1]
            constraints["foreign_key"] = ref
            i += 2
        elif token == "DEFAULT":
            default_val, consumed = _parse_default_value(tokens, i + 1)
            constraints["default"] = default_val
            i += 1 + consumed
        else:
            i += 1
    return constraints


def _parse_column_def(part: str) -> dict[str, Any] | None:
    part = part.strip()
    if not part:
        return None
    tokens = part.split()
    if not tokens:
        return None
    col_name = tokens[0]
    constraint_keywords = {
        "PRIMARY",
        "NOT",
        "DEFAULT",
        "UNIQUE",
        "REFERENCES",
        "CHECK",
        "CONSTRAINT",
        "GENERATED",
    }
    type_token = None
    type_end_idx = 1
    for i in range(1, len(tokens)):
        t = tokens[i].upper()
        if t in constraint_keywords or t.startswith("--") or t.startswith("/*"):
            break
        if type_token is None:
            type_token = tokens[i]
        else:
            type_token = type_token + " " + tokens[i]
        type_end_idx = i + 1
    if type_token is None:
        return None
    col_type_raw = type_token.upper().strip()
    col_type = TYPE_MAP.get(col_type_raw, "Text")
    remaining_tokens = tokens[type_end_idx:]
    constraints = _parse_constraints(remaining_tokens)
    return {
        "name": col_name,
        "col_type": col_type,
        "constraints": constraints,
    }


def parse_create_tables(sql_text: str) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    table_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\)\s*;",
        re.DOTALL | re.IGNORECASE,
    )
    for match in table_pattern.finditer(sql_text):
        table_name = match.group(1)
        body = match.group(2).strip()
        columns: list[dict[str, Any]] = []
        table_constraints: list[dict[str, Any]] = []
        parts = _split_top_level_commas(body)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            upper = part.upper()
            if upper.startswith("UNIQUE("):
                inner = part[7:-1]
                cols = [c.strip() for c in inner.split(",")]
                table_constraints.append({"type": "UNIQUE", "columns": cols})
                continue
            if upper.startswith("PRIMARY KEY"):
                continue
            if upper.startswith("CHECK"):
                continue
            if upper.startswith("FOREIGN KEY"):
                continue
            col = _parse_column_def(part)
            if col:
                columns.append(col)
        tables.append(
            {
                "name": table_name,
                "columns": columns,
                "table_constraints": table_constraints,
            }
        )
    return tables


def _parse_index_columns(cols_str: str) -> list[str]:
    cols_str = cols_str.strip()
    parts = _split_top_level_commas(cols_str)
    return [p.strip() for p in parts]


def parse_indexes(sql_text: str) -> list[dict[str, Any]]:
    indexes: list[dict[str, Any]] = []
    idx_pattern = re.compile(
        r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)\s*\((.+?)\)\s*;",
        re.DOTALL | re.IGNORECASE,
    )
    for match in idx_pattern.finditer(sql_text):
        is_unique = match.group(1) is not None
        idx_name = match.group(2)
        table_name = match.group(3)
        cols_str = match.group(4)
        columns = _parse_index_columns(cols_str)
        indexes.append(
            {
                "name": idx_name,
                "table": table_name,
                "columns": columns,
                "unique": is_unique,
            }
        )
    return indexes
