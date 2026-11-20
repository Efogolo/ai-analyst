"""Profile a table: shape, types, nulls, ids, date ranges and small value sets.

`profile_table` profiles a Postgres table with aggregate SQL only (the normal path).
`profile_csv` profiles a CSV with pandas and is kept for local files.
"""

import json
import re
import sys
import textwrap
from datetime import date
from pathlib import Path

import pandas as pd
import yaml
from psycopg2 import sql

from helpers.db import get_connection

# Columns with this many distinct values or fewer get their full value counts listed.
LOW_CARDINALITY_MAX = 20

# Types profiled as dates. The database knows the type, so there is no need to guess from names.
DATE_TYPES = {"date", "timestamp without time zone", "timestamp with time zone"}

# Every data query must be an aggregate. A query that returns more rows than this is refused.
MAX_ROWS_RETURNED = LOW_CARDINALITY_MAX + 1
_AGGREGATE = re.compile(r"\b(count|min|max|sum|avg)\s*\(", re.IGNORECASE)


def is_date_column(name: str) -> bool:
    """Return True if the column name follows Beam's date naming (`date`, `*_date`, `*_at`)."""
    return name == "date" or name.endswith("_date") or name.endswith("_at")


def profile_csv(path: str | Path) -> dict:
    """Return a profile of one CSV: shape, types, nulls, ids, date ranges and small value sets.

    Use it when meeting a table for the first time, before any analysis.
    """
    path = Path(path)
    # Read the header first and pick date columns by their name suffix. Beam's
    # exports name dates consistently, and guessing from values is slow and error prone.
    header = pd.read_csv(path, nrows=0).columns
    date_cols = [c for c in header if is_date_column(c)]
    df = pd.read_csv(path, parse_dates=date_cols)

    columns = [
        {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_rate": round(float(df[col].isna().mean()), 4),
            "distinct": int(df[col].nunique()),
        }
        for col in df.columns
    ]

    # Take the first *_id column as the table's key; duplicates there mean the
    # table is not one row per id.
    id_column = next((c for c in df.columns if c.endswith("_id")), None)
    duplicate_ids = int(df[id_column].duplicated().sum()) if id_column else 0

    date_columns = []
    for col in date_cols:
        values = df[col].dropna()
        date_columns.append({
            "name": col,
            "min": values.min().isoformat() if len(values) else None,
            "max": values.max().isoformat() if len(values) else None,
        })

    low_cardinality = {}
    for col in df.columns:
        if col in date_cols or df[col].nunique() > LOW_CARDINALITY_MAX:
            continue
        # value_counts leaves nulls out; the null rate is already in the columns table.
        counts = df[col].value_counts()
        low_cardinality[col] = {str(k): int(v) for k, v in counts.items()}

    if id_column is None:
        grain_guess = None
    elif duplicate_ids == 0:
        grain_guess = f"one row per {id_column}"
    else:
        grain_guess = f"not one row per {id_column}; check the grain"

    return {
        "table": path.stem,
        "rows": len(df),
        "columns": columns,
        "id_column": id_column,
        "duplicate_ids": duplicate_ids,
        "date_columns": date_columns,
        "low_cardinality": low_cardinality,
        "grain_guess": grain_guess,
    }


def profile_to_markdown(result: dict) -> str:
    """Return a profile from profile_csv as a markdown note, ready for knowledge/beam/."""
    grain = result["grain_guess"] or "no id column found"
    lines = [
        f"# {result['table']}",
        "",
        f"Grain (a guess from the data, confirm it): {grain}. "
        f"{result['rows']:,} rows.",
        "",
        "## Columns",
        "",
        "| Name | Type | Null rate | Distinct |",
        "| --- | --- | --- | --- |",
    ]
    for col in result["columns"]:
        lines.append(
            f"| {col['name']} | {col['dtype']} | {col['null_rate']:.2%} "
            f"| {col['distinct']:,} |"
        )

    lines += ["", "## Date ranges", ""]
    if result["date_columns"]:
        for col in result["date_columns"]:
            lines.append(f"- `{col['name']}`: {col['min']} to {col['max']}")
    else:
        lines.append("- None")

    lines += ["", "## Low-cardinality values", ""]
    if result["low_cardinality"]:
        for name, counts in result["low_cardinality"].items():
            values = ", ".join(f"{k} ({v:,})" for k, v in counts.items())
            lines.append(f"- `{name}`: {values}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Meaning",
        "",
        "Fill in what each column means for the business.",
        "",
    ]
    return "\n".join(lines)


def _aggregate_query(cur, query: sql.Composable, params=None) -> list[tuple]:
    """Run a query against table data and return its rows, but only if it is an aggregate.

    This is a safety net, not a SQL parser: every query in this module is built from
    COUNT/MIN/MAX/SUM templates, and this refuses anything that is not, or that returns
    more than a handful of rows. It matters most for `public.sessions`, which is very
    large, but it applies to every table.
    """
    text = query.as_string(cur)
    if not _AGGREGATE.search(text):
        raise ValueError(f"Refusing a non-aggregate query against table data: {text[:120]}")
    cur.execute(text, params)
    rows = cur.fetchmany(MAX_ROWS_RETURNED + 1)
    if len(rows) > MAX_ROWS_RETURNED:
        raise ValueError(f"Aggregate returned more than {MAX_ROWS_RETURNED} rows; refusing.")
    return rows


def _key_columns(cur, schema: str, table: str, column_names: list[str]) -> tuple[list[str], bool]:
    """Return (key columns, whether the database declares them as the primary key).

    With no declared primary key (views, some marts), fall back to the first `*_id` column, which
    the duplicate check then tests. With neither, raise instead of guessing a grain.
    """
    regclass = sql.Identifier(schema, table).as_string(cur)
    cur.execute(
        """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY (i.indkey)
        WHERE i.indrelid = %s::regclass AND i.indisprimary
        ORDER BY array_position(i.indkey::int2[], a.attnum)
        """,
        (regclass,),
    )
    declared = [row[0] for row in cur.fetchall()]
    if declared:
        return declared, True
    guess = next((c for c in column_names if c.endswith("_id")), None)
    if guess is None:
        raise ValueError(
            f"{schema}.{table} has no declared primary key and no *_id column, so its key "
            "cannot be guessed. Ask which column(s) identify a row, then pass them as key_columns."
        )
    return [guess], False


def profile_table(schema: str, table: str, key_columns: list[str] | None = None) -> dict:
    """Return a profile of one Postgres table using aggregate SQL only.

    Same facts as profile_csv: row count, null rate and distinct count per column, min/max for
    date columns, full value counts for low-cardinality columns, and a duplicate-key check.
    Never selects raw rows, so it is safe on `public.sessions`. Pass `key_columns` to name the key
    yourself when the table has no primary key and no `*_id` column.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema, table),
            )
            meta = cur.fetchall()
            if not meta:
                raise ValueError(f"{schema}.{table} not found in information_schema.")
            names = [name for name, _ in meta]
            dtypes = dict(meta)
            date_cols = [n for n in names if dtypes[n] in DATE_TYPES]
            if key_columns:
                unknown = [k for k in key_columns if k not in names]
                if unknown:
                    raise ValueError(f"{schema}.{table} has no column(s): {', '.join(unknown)}")
                key_cols, declared_pk = list(key_columns), False
            else:
                key_cols, declared_pk = _key_columns(cur, schema, table, names)
            source = sql.Identifier(schema, table)

            # One pass over the table for every per-column fact. COUNT(DISTINCT) on a
            # single-column primary key is skipped: it is the row count by definition.
            parts = [sql.SQL("COUNT(*)")]
            single_pk = key_cols[0] if declared_pk and len(key_cols) == 1 else None
            for name in names:
                col = sql.Identifier(name)
                parts.append(sql.SQL("COUNT({})").format(col))
                if name != single_pk:
                    parts.append(sql.SQL("COUNT(DISTINCT {})").format(col))
                if name in date_cols:
                    parts.append(sql.SQL("MIN({}), MAX({})").format(col, col))
            stats_query = sql.SQL("SELECT {} FROM {}").format(sql.SQL(", ").join(parts), source)
            row = _aggregate_query(cur, stats_query)[0]

            rows, pos = int(row[0]), 1
            columns, date_columns, distinct_of = [], [], {}
            for name in names:
                non_null = int(row[pos])
                pos += 1
                if name == single_pk:
                    distinct = rows
                else:
                    distinct = int(row[pos])
                    pos += 1
                if name in date_cols:
                    low, high = row[pos], row[pos + 1]
                    pos += 2
                    date_columns.append({
                        "name": name,
                        "min": low.isoformat() if low is not None else None,
                        "max": high.isoformat() if high is not None else None,
                    })
                distinct_of[name] = distinct
                columns.append({
                    "name": name,
                    "dtype": dtypes[name],
                    "null_rate": round((rows - non_null) / rows, 4) if rows else 0.0,
                    "distinct": distinct,
                })

            # Duplicate keys: a declared primary key cannot repeat, so only check undeclared ones.
            duplicate_rows = 0
            if key_cols and not declared_pk:
                keys = sql.SQL(", ").join(sql.Identifier(k) for k in key_cols)
                dup_query = sql.SQL(
                    "SELECT COALESCE(SUM(c - 1), 0) FROM "
                    "(SELECT COUNT(*) AS c FROM {} GROUP BY {} HAVING COUNT(*) > 1) d"
                ).format(source, keys)
                duplicate_rows = int(_aggregate_query(cur, dup_query)[0][0])

            # Full value counts for small value sets. Nulls are left out; the null rate has them.
            low_cardinality = {}
            for name in names:
                if name in date_cols or name in key_cols:
                    continue
                if not 0 < distinct_of[name] <= LOW_CARDINALITY_MAX:
                    continue
                col = sql.Identifier(name)
                value_query = sql.SQL(
                    "SELECT {col}, COUNT(*) FROM {src} WHERE {col} IS NOT NULL "
                    "GROUP BY {col} ORDER BY COUNT(*) DESC"
                ).format(col=col, src=source)
                low_cardinality[name] = {
                    str(value): int(count) for value, count in _aggregate_query(cur, value_query)
                }
    finally:
        conn.close()

    key_label = ", ".join(key_cols)
    if duplicate_rows == 0:
        grain_guess = f"one row per {key_label}"
    else:
        grain_guess = f"not one row per {key_label}; check the grain"

    return {
        "schema": schema,
        "table": table,
        "rows": rows,
        "columns": columns,
        "id_column": key_label,
        "key_columns": key_cols,
        "declared_primary_key": declared_pk,
        "duplicate_ids": duplicate_rows,
        "date_columns": date_columns,
        "low_cardinality": low_cardinality,
        "grain_guess": grain_guess,
    }


BEGIN_MARKER = "# --- BEGIN profile (auto-generated by /profile \u2014 do not hand-edit) ---"
END_MARKER = "# --- END profile ---"
_MARKED_BLOCK = re.compile(
    rf"^{re.escape(BEGIN_MARKER)}\n.*?^{re.escape(END_MARKER)}\n?", re.MULTILINE | re.DOTALL
)
# A `profile:` block with no markers, from before markers existed. Replaced once, then marked.
_LEGACY_BLOCK = re.compile(r"^profile:[^\n]*\n(?:[ \t][^\n]*\n|\n)*", re.MULTILINE)


def update_yaml_profile(path: str | Path, result: dict, as_of: str | None = None) -> Path:
    """Write the generated facts from profile_table into a table's YAML under a `profile:` key.

    The block sits between BEGIN/END marker comments. Only what is between them is replaced, or
    the block is appended if it is missing. Every other line of the file, including comments and
    hand-written descriptions, is left byte for byte as it was. The file is edited as text on
    purpose: loading and dumping it with PyYAML would drop its comments.
    """
    path = Path(path)
    as_of = as_of or date.today().isoformat()
    dates = {d["name"]: d for d in result["date_columns"]}
    columns = {}
    for col in result["columns"]:
        entry = {"null_rate": col["null_rate"], "distinct": col["distinct"]}
        if col["name"] in dates:
            entry["min"], entry["max"] = dates[col["name"]]["min"], dates[col["name"]]["max"]
        if col["name"] in result["low_cardinality"]:
            entry["values"] = result["low_cardinality"][col["name"]]
        columns[col["name"]] = entry

    body = {
        "as_of": as_of,
        "rows": result["rows"],
        "key": {
            "columns": result["key_columns"],
            "declared_primary_key": result["declared_primary_key"],
            "duplicate_rows": result["duplicate_ids"],
        },
        "grain_guess": result["grain_guess"],
        "columns": columns,
    }
    dumped = yaml.safe_dump(body, sort_keys=False, default_flow_style=False, allow_unicode=True)
    block = f"{BEGIN_MARKER}\nprofile:\n{textwrap.indent(dumped, '  ')}{END_MARKER}\n"

    text = path.read_text()
    if text.count(BEGIN_MARKER) != text.count(END_MARKER) or text.count(BEGIN_MARKER) > 1:
        raise ValueError(f"{path}: profile markers are unbalanced or repeated; fix by hand.")
    if _MARKED_BLOCK.search(text):
        text = _MARKED_BLOCK.sub(lambda _: block, text, count=1)
    elif _LEGACY_BLOCK.search(text):
        text = _LEGACY_BLOCK.sub(lambda _: block, text, count=1)
    else:
        text = text.rstrip("\n") + "\n\n" + block
    path.write_text(text)
    return path


if __name__ == "__main__":
    args = sys.argv[1:]
    save_to = None
    if "--save-json" in args:
        i = args.index("--save-json")
        save_to = args[i + 1] if i + 1 < len(args) else None
        del args[i : i + 2]
    key_override = None
    if "--key" in args:
        i = args.index("--key")
        key_override = args[i + 1].split(",") if i + 1 < len(args) else None
        del args[i : i + 2]
    if len(args) != 1 or (save_to is None and "--save-json" in sys.argv) or (
        key_override is None and "--key" in sys.argv
    ):
        sys.exit("usage: python helpers/profile.py <schema.table> [--key col[,col]] [--save-json PATH]")
    target = args[0]
    if target.endswith(".csv"):
        result = profile_csv(target)
    else:
        schema_name, _, table_name = target.rpartition(".")
        if not schema_name:
            sys.exit("Give the table as schema.table, for example public.users")
        result = profile_table(schema_name, table_name, key_override)
    output = json.dumps(result, indent=2, default=str)
    if save_to:
        Path(save_to).write_text(output)
    print(output)
