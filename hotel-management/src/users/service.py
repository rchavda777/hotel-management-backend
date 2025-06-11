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
                "user_role": result[2],
                "profile_completed": False,
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

def complete_profile(user_id: int, profile_data: dict):
    """
    Complete the user profile based on user role (guest or staff)
    """
    conn = get_db_connection()
    if not conn:
        return {
            "status": "error",
            "message": "Database connection failed"
        }

    try:
        with conn.cursor() as cur:
            # First check if user exists and get their role
            cur.execute("SELECT user_role FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                raise ValueError("User not found")
            
            user_role = user[0]
            
            # Complete profile based on user role
            if user_role == "staff":
                required_fields = ["first_name", "last_name", "date_of_birth", 
                                "address", "position_id", "hire_date"]
                for field in required_fields:
                    if field not in profile_data:
                        raise ValueError(f"Missing required field for staff: {field}")
                
                cur.execute("""
                    INSERT INTO staff_profiles (
                        user_id, first_name, last_name, date_of_birth, 
                        address, position_id, hire_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        date_of_birth = EXCLUDED.date_of_birth,
                        address = EXCLUDED.address,
                        position_id = EXCLUDED.position_id,
                        hire_date = EXCLUDED.hire_date
                """, (
                    user_id,
                    profile_data["first_name"],
                    profile_data["last_name"],
                    profile_data["date_of_birth"],
                    profile_data["address"],
                    profile_data["position_id"],
                    profile_data["hire_date"]
                ))
                
            elif user_role == "guest":
                required_fields = ["first_name", "last_name", "date_of_birth", "address"]
                for field in required_fields:
                    if field not in profile_data:
                        raise ValueError(f"Missing required field for guest: {field}")
                
                cur.execute("""
                    INSERT INTO guest_profiles (
                        user_id, first_name, last_name, 
                        date_of_birth, address, preferences
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        date_of_birth = EXCLUDED.date_of_birth,
                        address = EXCLUDED.address,
                        preferences = EXCLUDED.preferences
                """, (
                    user_id,
                    profile_data["first_name"],
                    profile_data["last_name"],
                    profile_data["date_of_birth"],
                    profile_data["address"],
                    json.dumps(profile_data.get("preferences", {}))
                ))
            
            else:
                raise ValueError("Invalid user role")
            
            # Mark profile as completed
            cur.execute("""
                UPDATE users SET profile_completed = TRUE WHERE id = %s
            """, (user_id,))
            
            conn.commit()
            return {
                "status": "success",
                "message": f"{user_role} profile completed successfully"
            }
            
    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        conn.close()