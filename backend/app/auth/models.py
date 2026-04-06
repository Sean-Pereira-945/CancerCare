from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    cancer_type: str = ""
    role: str = "patient"  # or 'caregiver'


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    cancer_type: str = ""
    role: str = "patient"
