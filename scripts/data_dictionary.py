"""Generate the dictionary from static SQLAlchemy metadata, without a database."""

from pathlib import Path

from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateIndex, CreateTable

from services.api.db.models import metadata

lines = [
    "# Data dictionary",
    "",
    "Generated from static mappings; matches frozen v1.0 DDL (see schema-provenance.md).",
    "",
    "Scores/money use Decimal; JSON decimal values must be strings. All timestamps are timezone-aware.",
    "",
]
for table in sorted(metadata.tables.values(), key=lambda t: t.name):
    lines += [
        f"## {table.name}",
        "",
        "| Column | PostgreSQL type | Nullable | Default |",
        "|---|---|---|---|",
    ]
    for col in table.columns:
        default = (
            str(col.server_default.arg)
            if col.server_default is not None and col.identity is None
            else ("IDENTITY" if col.identity is not None else "")
        )
        lines.append(
            f"| {col.name} | {col.type.compile(dialect=dialect())} | {col.nullable} | {default} |"
        )
    lines += [
        "",
        "```sql",
        str(CreateTable(table).compile(dialect=dialect())).strip() + ";",
        "```",
        "",
    ]
    for index in sorted(table.indexes, key=lambda i: i.name):
        lines += ["```sql", str(CreateIndex(index).compile(dialect=dialect())) + ";", "```", ""]
Path("docs/data-dictionary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
