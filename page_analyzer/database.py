import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """ connection to DB """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except psycopg2.OperationalError as error:
        print(f"Error connecting to database: {error}")
        return None

def close_db_connection(conn):
    if conn is not None:
        conn.close()
