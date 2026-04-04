import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        database=os.getenv("PG_DB", "pharmacy"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASS", "postgres"),
        port=int(os.getenv("PG_PORT", "5432")),
        cursor_factory=RealDictCursor
    )
