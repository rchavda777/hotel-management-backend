from users.utils import decode_jwt_token

def get_authenticated_user(event):
    auth_header = event.get("headers", {}).get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise Exception("Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    # Validate JWT token and extract user info
    decoded_token = decode_jwt_token(token)
    if not decoded_token or "user_id" not in decoded_token:
        raise Exception("Invalid or expired token")

    return {
        "user_id": decoded_token["user_id"],
        "role": decoded_token.get("role")
    }
