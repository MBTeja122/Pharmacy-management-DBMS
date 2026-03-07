import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="Pharmacy",
        user="postgres",
        password="your_password",
        cursor_factory=RealDictCursor
    )
