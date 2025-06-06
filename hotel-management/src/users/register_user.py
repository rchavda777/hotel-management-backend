import json
from users.service import register_user

def register_user_handler(event, context):
    """
    Lambda handler function to register a new user.
    Args:
        event (dict): Event data containing user registration details.
    Returns:
        dict: Response containing the status of the registration.
    """
    try:
        body = json.loads(event["body"])
        response = register_user(body)

        status_code = 200 if response["status"] == "success" else 400
        return {
            "statusCode": status_code,
            "body": json.dumps(response),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }
