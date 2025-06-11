import bcrypt
import os

from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY","d4f7e3a9b0124c789e0f15b4c6a7d9e8f1c2b3d4e5f60718293a4b5c6d7e8f90")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in the .env file")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(user_id, role):
    expire = datetime.utcnow() + timedelta(hours=1)  # 🔒 Valid for 1 hour
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise Exception("Token has expired")
    except JWTError:
        raise Exception("Invalid token")