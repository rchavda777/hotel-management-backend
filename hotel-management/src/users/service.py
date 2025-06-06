import json

from db.db_connection import get_db_connection
from users.utils import hash_password, verify_password, create_jwt_token

def register_user(data):
    """
    Register a new user and create s their profile (guest or staff).
    """

    username = data["username"]
    email = data["email"]
    password = data["password"]
    user_role = data.get("user_role", "guest") # Default to 'guest' if not provided

    if not username or not email or not password:
        return {
            "status": "error",
            "message": "Username, email, and password are required"
        }

    conn = get_db_connection()
    if not conn:
        return {
            "status": "error",
            "message": "Database connection failed"
        } 

    try:
        hashed_pass = hash_password(password)

        with conn.cursor() as cur:
            # Check if the username or email already exists
            cur.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                        (username, email))
            if cur.fetchone():
                raise ValueError("Username or email already exists")
            
            cur.execute("""
                INSERT INTO users (username, email, password, user_role)
                VALUES (%s, %s, %s, %s) RETURNING id, username;
            """, (username, email, hashed_pass, user_role))

            result = cur.fetchone()
            conn.commit()
            return {
                "id": result[0],
                "username": result[1],
                "status": "success"
            }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        conn.close()


def login_user(email: str, password: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password, user_role FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user is None:
                raise Exception("User not found")
            
            user_id, hashed_password, role = user
            if not verify_password(password, hashed_password):
                raise Exception("Invalid password")
            
            token = create_jwt_token(user_id, role) 
            return {"access_token": token, "token_type": "bearer"}