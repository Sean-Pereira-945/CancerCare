from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.models import RegisterRequest, LoginRequest
from app.auth.utils import hash_password, verify_password, create_access_token, decode_token
from app.database import get_supabase

router = APIRouter()
security = HTTPBearer()


@router.post("/register")
async def register(data: RegisterRequest):
    """Register a new patient or caregiver account."""
    sb = get_supabase()

    # Check if user exists
    existing = sb.table("users").select("id").eq("email", data.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = sb.table("users").insert({
        "name": data.name,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "cancer_type": data.cancer_type,
        "role": data.role
    }).execute()

    token = create_access_token({"sub": user.data[0]["id"], "role": data.role})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
async def login(data: LoginRequest):
    """Login with email and password, returns JWT token."""
    sb = get_supabase()
    user = sb.table("users").select("*").eq("email", data.email).execute()

    if not user.data or not verify_password(data.password, user.data[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.data[0]["id"],
        "role": user.data[0]["role"]
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.data[0]["id"],
            "name": user.data[0]["name"],
            "email": user.data[0]["email"],
            "cancer_type": user.data[0].get("cancer_type", ""),
            "role": user.data[0]["role"]
        }
    }


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to extract and validate JWT token from request headers."""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload
