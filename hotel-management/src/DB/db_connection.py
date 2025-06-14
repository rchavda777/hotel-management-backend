import os
import psycopg2

from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            database=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ.get("POSTGRES_PORT", "5432"),
            connect_timeout=10,
            cursor_factory=RealDictCursor
        )
        print("Database connection established successfully.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise



