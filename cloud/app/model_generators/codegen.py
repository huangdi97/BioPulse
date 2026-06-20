from typing import Any


def column_to_sa(col: dict[str, Any]) -> str:
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
