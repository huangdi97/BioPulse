import importlib.util
from pathlib import Path

from cloud.app.model_generators.codegen import column_to_sa
from cloud.app.model_generators.parser import parse_create_tables, parse_indexes


def _import_ddl_modules() -> list[str]:
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


def generate_models(output_path: str = "cloud/app/models.py") -> None:
    sql_strings = _import_ddl_modules()
    full_sql = "\n".join(sql_strings)
    tables = parse_create_tables(full_sql)
    indexes = parse_indexes(full_sql)
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
        unique_cols: list[str] = []
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
    body = "\n\n\n".join(lines)
    index_defs: list[str] = []
    for idx in indexes:
        cols_list = ", ".join(f'"{c}"' for c in idx["columns"])
        unique_arg = ", unique=True" if idx["unique"] else ""
        index_defs.append(f'Index("{idx["name"]}", {cols_list}{unique_arg})')
    if index_defs:
        body += "\n\n\n" + "\n\n".join(index_defs)
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
