from fastapi import Request, HTTPException
from itsdangerous import TimestampSigner, BadSignature
import os

SECRET = os.environ.get("SPARKTRACK_SECRET", "dev-secret")
signer = TimestampSigner(SECRET)

def create_token(username: str) -> str:
    return signer.sign(username.encode()).decode()

def verify_token(token: str) -> str:
    try:
        return signer.unsign(token, max_age=60*60*24*7).decode()
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        return verify_token(token)
    except HTTPException:
        return None
