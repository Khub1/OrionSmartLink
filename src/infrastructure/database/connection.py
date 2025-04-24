import pyodbc
from src.config.settings import DATABASE_SETTINGS

def create_db_connection():
    conn_str = (
        f"DRIVER={{{DATABASE_SETTINGS['driver']}}};"
        f"SERVER={DATABASE_SETTINGS['server']};"
        f"DATABASE={DATABASE_SETTINGS['name']};"
        f"UID={DATABASE_SETTINGS['user']};"
        f"PWD={DATABASE_SETTINGS['password']}"
    )
    try:
        conn = pyodbc.connect(conn_str)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
