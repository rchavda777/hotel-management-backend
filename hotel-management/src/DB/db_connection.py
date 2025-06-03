import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432") ,
            connect_timeout=10
        )
        print("Database connection established successfully.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise



