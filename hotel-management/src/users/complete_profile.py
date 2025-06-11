import json
from users.service import complete_profile
from middleware.jwt_auth import get_authenticated_user

def complete_profile_handler(event, context):
    """
    Protected endpoint to complete the user profile.
    Requires a valid JWT token in the Authorization header.
    
    Returns:
    - 200: Profile completed successfully
    - 400: Bad request (invalid data)
    - 401: Unauthorized (missing/invalid token)
    - 403: Forbidden (valid token but insufficient permissions)
    - 500: Server error
    """
    # Set default headers
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"  # Adjust for production
    }

    try:
        # 🔐 Strict authentication check
        try:
            user = get_authenticated_user(event)
            if not user or not user.get("user_id"):
                return {
                    "statusCode": 401,
                    "body": json.dumps({
                        "status": "error",
                        "message": "Invalid authentication credentials"
                    }),
                    "headers": headers
                }
        except Exception as auth_error:
            return {
                "statusCode": 401,
                "body": json.dumps({
                    "status": "error",
                    "message": str(auth_error)
                }),
                "headers": headers
            }

        # ✅ Validate request body
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "status": "error",
                    "message": "Invalid JSON format in request body"
                }),
                "headers": headers
            }

        # 🚫 Prevent user_id override
        if "user_id" in body:
            return {
                "statusCode": 403,
                "body": json.dumps({
                    "status": "error",
                    "message": "Cannot modify user_id"
                }),
                "headers": headers
            }

        # 🛡️ Process profile completion
        response = complete_profile(user["user_id"], body)

        # Return appropriate status code based on service response
        status_code = 200 if response.get("status") == "success" else 400
        return {
            "statusCode": status_code,
            "body": json.dumps(response),
            "headers": headers
        }

    except Exception as e:
        # Log the full error for debugging
        print(f"Server Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": "Internal server error"
            }),
            "headers": headers
        }