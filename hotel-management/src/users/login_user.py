import json
from users.service import login_user

def login_user_handler(event, context):
    try:
        body = json.loads(event["body"])
        email = body.get("email")
        password = body.get("password")
        if not email or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Email and password required"})
            }
        
        token = login_user(email, password)
        return {
            "statusCode": 200,
            "body": json.dumps(token)
        }
    except Exception as e:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)})
        }
