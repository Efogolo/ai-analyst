"""Direct, read-only Postgres access for scripts.

The course-db MCP tools only exist inside a Claude conversation; a standalone script
cannot import them. Anything that must be rerunnable connects here instead, using the
POSTGRES_* environment variables. Credentials are never written into code.
"""

import os
import warnings

import pandas as pd
import psycopg2

REQUIRED_ENV = (
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DATABASE",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)


def get_connection():
    """Open a read-only psycopg2 connection from the POSTGRES_* environment variables."""
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Set these environment variables first: {', '.join(missing)}")
    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DATABASE"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    )
    # A script that analyses data has no business writing to it.
    conn.set_session(readonly=True)
    return conn


def read_sql(sql: str, params=None) -> pd.DataFrame:
    """Run one query with pandas.read_sql and return a DataFrame, closing the connection.

    pandas warns when handed a raw psycopg2 connection instead of a SQLAlchemy engine.
    The query still runs correctly, so that one warning is silenced here.
    """
    conn = get_connection()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")
            return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
