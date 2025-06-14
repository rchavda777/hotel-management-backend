import json

from db.db_connection import get_db_connection
from db.db_common_query import get_by_column, insert_row, upsert_row, get_by_id, update_by_id
from users.utils import hash_password, verify_password, create_jwt_token

def register_user(data):
    """
    Register a new user and create s their profile (guest or staff).
    Args:
        - username: Unique username
        - email: User's email address
        - password: User's password
        - user_role: Role of the user ('guest' or 'staff'). Defaults to 'guest'.
    Returns:
        Dictionary with status and user's data.
    """

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
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

    # Check if username or email already exists
    existing_by_username = get_by_column("users", "username", username)
    existing_by_email = get_by_column("users", "email", email)

    if existing_by_username or existing_by_email:
        return {
            "status": "error",
            "message": "Username or email already exists"
        }
    
    # Hash password and insert new user into database
    try:
        hashed_password = hash_password(password)
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "user_role": user_role
        }

        result = insert_row("users", user_data, returning="id, username, email, user_role, profile_completed")

        if result:
            return {
                "status": "success",
                **result
            }
        else:
            return {
                "status": "error",
                "message": "User registration failed"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }


def login_user(email: str, password: str):
    """
    Login user with email and password.
    On suceesful login, generate and return JWT token.
    """
    # Check if user exists
    user = get_by_column("users", "email", email)

    if not user:
        raise Exception("User not found")
    
    if not verify_password(password, user["password"]):
        raise Exception("Invalid password")

    token = create_jwt_token(user["id"], user["user_role"])
    return {"access_token": token, "token_type": "bearer"}


def complete_profile(user_id: int, profile_data: dict):
    """
    Complete the user profile based on user role (guest or staff)
    using reusable db_common_query functions.
    """
    # Get user and role
    user = get_by_id("users", user_id)
    if not user:
        return {"status": "error", "message": "User not found"}

    user_role = user.get("user_role")

    #  Validate and upsert profile based on role
    if user_role == "staff":
        required_fields = ["first_name", "last_name", "date_of_birth", 
                           "address", "position_id", "hire_date"]
        for field in required_fields:
            if field not in profile_data:
                return {"status": "error", "message": f"Missing field: {field}"}

        staff_data = {
            "user_id": user_id,
            "first_name": profile_data["first_name"],
            "last_name": profile_data["last_name"],
            "date_of_birth": profile_data["date_of_birth"],
            "address": profile_data["address"],
            "position_id": profile_data["position_id"],
            "hire_date": profile_data["hire_date"]
        }

        upsert_row(
            table="staff_profiles",
            data=staff_data,
            conflict_column="user_id",
            update_columns=[
                "first_name", "last_name", "date_of_birth",
                "address", "position_id", "hire_date"
            ],
            returning="user_id"
        )

    elif user_role == "guest":
        required_fields = ["first_name", "last_name", "date_of_birth", "address"]
        for field in required_fields:
            if field not in profile_data:
                return {"status": "error", "message": f"Missing field: {field}"}

        guest_data = {
            "user_id": user_id,
            "first_name": profile_data["first_name"],
            "last_name": profile_data["last_name"],
            "date_of_birth": profile_data["date_of_birth"],
            "address": profile_data["address"],
            "preferences": json.dumps(profile_data.get("preferences", {}))
        }

        upsert_row(
            table="guest_profiles",
            data=guest_data,
            conflict_column="user_id",
            update_columns=[
                "first_name", "last_name", "date_of_birth",
                "address", "preferences"
            ],
            returning="user_id"
        )

    else:
        return {"status": "error", "message": "Invalid user role"}

    # Mark profile as complete using update_by_id
    update_by_id(
        table="users",
        row_id=user_id,
        data={"profile_completed": True},
        returning=None
    )

    return {
        "status": "success",
        "message": f"{user_role} profile completed successfully"
    }

