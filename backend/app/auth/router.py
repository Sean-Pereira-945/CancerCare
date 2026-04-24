from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.models import RegisterRequest, LoginRequest
from app.auth.utils import hash_password, verify_password, create_access_token, decode_token
from app.database import get_db
from app.models.db import User
from sqlalchemy.orm import Session

router = APIRouter()
security = HTTPBearer()


@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new patient or caregiver account."""
    # Check if user exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        cancer_type=data.cancer_type,
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password, returns JWT token."""
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "cancer_type": user.cancer_type or "",
            "role": user.role
        }
    }


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to extract and validate JWT token from request headers."""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload
