from users.utils import decode_jwt_token

def jwt_auth_middleware(event):
    """
    Extract and validate the JWT token from the Authorization header.
    Returns user data if valid, oor an error response if not.
    """

    headers = event.get("headers", {})
    auth_header = headers.get("Authorization", "")

    if not auth_header or not auth_header.startswith("Bearer "):
        return {
            "statusCode": 401,
            "body": "Unauthorized: Missing or invalid Authorization header",
            "heders": {
                "content-type": "application/json"
            }
        }

    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)

    if "error" in payload:
        return {
            "statusCode": 401,
            "body": payload["error"],
            "headers": {
                "content-type": "application/json"
            }
        }

    return payload  # Return the decoded payload if valid
    