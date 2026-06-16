"""从 DDL SQL 文件中读取所有 CREATE TABLE 语句，生成 SQLAlchemy Table 定义写入 models.py"""

import importlib.util
import re
from pathlib import Path
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


def _import_ddl_modules() -> list[str]:
    """从 cloud.app.schemas.ddl 导入所有 SQL 字符串，返回拼接列表"""
    pkg = "cloud.app.schemas.ddl"
    ddl_dir = Path(importlib.util.find_spec(pkg).submodule_search_locations[0])
    sql_strings: list[str] = []
    for mod_file in sorted(ddl_dir.glob("*.py")):
        if mod_file.name == "__init__.py":
            continue
        mod_name = f"{pkg}.{mod_file.stem}"
        mod = importlib.import_module(mod_name)
        for attr_name in dir(mod):
            if attr_name.endswith("_SQL"):
                sql_strings.append(getattr(mod, attr_name))
    return sql_strings


def parse_create_tables(sql_text: str) -> list[dict[str, Any]]:
    """
    解析 SQL 文本中的 CREATE TABLE 语句。

    返回列表，每项包含:
    - name: 表名
    - columns: 列定义列表，每项包含 name, col_type, constraints
    - table_constraints: 表级约束 (UNIQUE, PRIMARY KEY 等)
    """
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

        # Split by top-level commas (not inside parentheses)
        parts = _split_top_level_commas(body)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            upper = part.upper()

            # Table-level constraints
            if upper.startswith("UNIQUE("):
                # UNIQUE(col1, col2)
                inner = part[7:-1]
                cols = [c.strip() for c in inner.split(",")]
                table_constraints.append({"type": "UNIQUE", "columns": cols})
                continue

            if upper.startswith("PRIMARY KEY"):
                # PRIMARY KEY (col) - handle if needed
                continue

            if upper.startswith("CHECK"):
                continue

            if upper.startswith("FOREIGN KEY"):
                continue

            # Regular column definition
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


def _split_top_level_commas(text: str) -> list[str]:
    """Split by commas that are not inside parentheses."""
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


def _parse_column_def(part: str) -> dict[str, Any] | None:
    """
    解析单列定义。
    返回 dict 包含 name, col_type, constraints dict。
    """
    # Remove leading/trailing whitespace
    part = part.strip()
    if not part:
        return None

    # Split on first whitespace to get column name
    tokens = part.split()
    if not tokens:
        return None

    col_name = tokens[0]

    # Find the type (second token, unless it starts with a constraint keyword)
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
            # Compound types like UNSIGNED INTEGER, or TIMESTAMP
            type_token = type_token + " " + tokens[i]
        type_end_idx = i + 1

    if type_token is None:
        return None

    # Normalize type
    col_type_raw = type_token.upper().strip()
    # Map to SQLAlchemy type
    col_type = TYPE_MAP.get(col_type_raw, "Text")

    # Parse constraints from remaining tokens
    remaining_tokens = tokens[type_end_idx:]
    constraints = _parse_constraints(remaining_tokens)

    return {
        "name": col_name,
        "col_type": col_type,
        "constraints": constraints,
    }


def _parse_constraints(tokens: list[str]) -> dict[str, Any]:
    """Parse constraints from remaining tokens after column name and type."""
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


def _parse_default_value(tokens: list[str], start: int) -> tuple[str | None, int]:
    """Parse DEFAULT value from tokens starting at start index."""
    if start >= len(tokens):
        return None, 0

    token = tokens[start]
    # Handle quoted string: 'abc' or "abc"
    if token.startswith("'") or token.startswith('"'):
        # Could be 'abc' or 'abc', or "abc"
        # Handle escaped quotes
        quote_char = token[0]
        # Find the closing quote
        if len(token) > 1 and token.endswith(quote_char) and not token.endswith("\\" + quote_char):
            return token, 1
        # Multi-token quoted string
        parts = [token]
        for j in range(start + 1, len(tokens)):
            parts.append(tokens[j])
            if tokens[j].endswith(quote_char) and not tokens[j].endswith("\\" + quote_char):
                break
        return " ".join(parts), len(parts)

    # Handle CURRENT_TIMESTAMP
    if token.upper() == "CURRENT_TIMESTAMP":
        return "CURRENT_TIMESTAMP", 1

    # Handle numeric literal
    if re.match(r"^-?\d+(\.\d+)?$", token):
        return token, 1

    # Handle NULL
    if token.upper() == "NULL":
        return "NULL", 1

    # Handle other identifiers (e.g. function calls)
    return token, 1


def parse_indexes(sql_text: str) -> list[dict[str, Any]]:
    """解析 SQL 文本中的 CREATE INDEX 语句。"""
    indexes: list[dict[str, Any]] = []

    # Match CREATE INDEX and CREATE UNIQUE INDEX
    idx_pattern = re.compile(
        r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)\s*\((.+?)\)\s*;",
        re.DOTALL | re.IGNORECASE,
    )

    for match in idx_pattern.finditer(sql_text):
        is_unique = match.group(1) is not None
        idx_name = match.group(2)
        table_name = match.group(3)
        cols_str = match.group(4)

        # Parse columns (handle functions like MIN(a), MAX(b))
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


def _parse_index_columns(cols_str: str) -> list[str]:
    """Parse index column list, handling function calls."""
    cols_str = cols_str.strip()
    parts = _split_top_level_commas(cols_str)
    return [p.strip() for p in parts]


def column_to_sa(col: dict[str, Any]) -> str:
    """
    将列定义转换为 SQLAlchemy Column(...) 字符串。
    """
    name = col["name"]
    col_type = col["col_type"]
    cons = col["constraints"]

    args = [f'Column("{name}", {col_type}']

    if cons["foreign_key"]:
        fk = cons["foreign_key"].replace("(", ".").replace(")", "")
        args.append(f'ForeignKey("{fk}")')

    if cons["primary_key"]:
        args.append("primary_key=True")
    if cons["autoincrement"]:
        args.append("autoincrement=True")
    if not cons["nullable"] and not cons["primary_key"]:
        args.append("nullable=False")
    if cons["unique"] and not cons["primary_key"]:
        args.append("unique=True")
    if cons["default"] is not None:
        default_val = cons["default"]
        if default_val == "NULL":
            pass
        elif default_val == "CURRENT_TIMESTAMP":
            args.append("server_default=text('CURRENT_TIMESTAMP')")
        elif default_val.startswith("'") or default_val.startswith('"'):
            inner = default_val[1:-1]
            inner_escaped = inner.replace("'", "\\'")
            args.append(f"server_default=text('{inner_escaped}')")
        else:
            args.append(f"server_default=text(\"'\"'{default_val}'\"'\")")

    return ", ".join(args) + ")"


def generate_header_and_metadata(used_types: set[str]) -> str:
    """生成文件头部 imports 和 metadata 定义。"""
    imports = [
        "from sqlalchemy import MetaData, Table, Column",
    ]

    extra_types = []
    for t in sorted(used_types):
        if t not in (
            "Integer",
            "Float",
            "Text",
            "LargeBinary",
        ):
            extra_types.append(t)
    if extra_types:
        imports[0] += ", " + ", ".join(extra_types)

    # Always ensure core types are imported
    core_types = ["Integer", "Float", "Text", "LargeBinary"]
    all_types = set(core_types) | used_types
    if "ForeignKey" in used_types:
        all_types.discard("ForeignKey")
    if "Index" in used_types:
        all_types.discard("Index")
    if "UniqueConstraint" in used_types:
        all_types.discard("UniqueConstraint")

    result = ""
    result += "from sqlalchemy import MetaData, Table, Column"
    extra = []
    for t in sorted(all_types):
        if t not in ("Integer", "Float", "Text", "LargeBinary", "MetaData", "Table", "Column"):
            extra.append(t)
    if extra:
        result += ", " + ", ".join(extra)

    result += "\n\n"
    result += "metadata = MetaData()\n\n"
    return result


def generate_models(output_path: str = "cloud/app/models.py") -> None:
    """
    主要生成函数：
    1. 读所有 DDL 文件
    2. 解析每个 CREATE TABLE
    3. 生成文件头（imports + metadata = MetaData()）
    4. 生成每个 Table(...) 定义
    5. 生成所有 Index(...) 定义
    6. 写入 output_path
    """
    sql_strings = _import_ddl_modules()
    full_sql = "\n".join(sql_strings)

    tables = parse_create_tables(full_sql)
    indexes = parse_indexes(full_sql)

    # Track what types/features are used
    used_types: set[str] = set()
    has_foreign_key = False
    has_unique_constraint = False
    has_index = len(indexes) > 0

    lines: list[str] = []

    for table in tables:
        table_name = table["name"]
        columns = table["columns"]
        table_constraints = table["table_constraints"]

        col_lines: list[str] = []
        for col in columns:
            cons = col["constraints"]
            used_types.add(col["col_type"])
            if cons["foreign_key"]:
                has_foreign_key = True
            col_lines.append(column_to_sa(col))

        # Handle table-level UNIQUE constraints
        unique_cols: list[dict[str, Any]] = []
        for tc in table_constraints:
            if tc["type"] == "UNIQUE":
                has_unique_constraint = True
                col_names = ", ".join(f'"{c}"' for c in tc["columns"])
                unique_cols.append(col_names)

        for uc in unique_cols:
            col_lines.append(f"            UniqueConstraint({uc})")

        cols_body = "\n".join(f"        {c}," for c in col_lines)
        table_block = f'Table(\n    "{table_name}",\n    metadata,\n{cols_body}\n)'
        lines.append(table_block)

    # Add blank line between tables
    body = "\n\n\n".join(lines)

    # Build Index definitions
    index_defs: list[str] = []
    for idx in indexes:
        cols_list = ", ".join(f'"{c}"' for c in idx["columns"])
        unique_arg = ", unique=True" if idx["unique"] else ""
        index_defs.append(f'Index("{idx["name"]}", {cols_list}{unique_arg})')

    if index_defs:
        body += "\n\n\n" + "\n\n".join(index_defs)

    # Build imports
    import_parts = ["MetaData", "Table", "Column"]
    for t in sorted(used_types):
        import_parts.append(t)
    if has_foreign_key:
        import_parts.append("ForeignKey")
    if has_unique_constraint:
        import_parts.append("UniqueConstraint")
    if has_index:
        import_parts.append("Index")
    import_parts.append("text")

    import_line = "from sqlalchemy import " + ", ".join(sorted(import_parts))
    header = import_line + "\n\nmetadata = MetaData()\n\n"

    full_output = header + body + "\n"

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_path_obj.write_text(full_output)
    print(f"Generated {output_path} with {len(tables)} tables and {len(indexes)} indexes")


if __name__ == "__main__":
    generate_models()
