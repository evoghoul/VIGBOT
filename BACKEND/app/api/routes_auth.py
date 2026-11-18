from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import LoginRequest, Token, StudentProfile
from app.database import DataRepository, DatabaseSession
from app.security import verify_password, create_access_token, get_current_student

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(req: LoginRequest):
    student = DataRepository.get_student_by_username(req.username)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student Registration Number not found. Please verify your Regd. Number.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enforce password rule: firstname@regdnumber (case-insensitive)
    full_name = student.get("full_name") or ""
    first_name = full_name.strip().split()[0] if full_name.strip() else ""
    roll_no = student.get("roll_no") or ""
    expected_pwd = f"{first_name}@{roll_no}".lower()

    input_pwd_clean = req.password.strip().lower()
    is_valid = (input_pwd_clean == expected_pwd) or verify_password(req.password, student.get("password_hash"))

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid password. Password must be firstname@regdnumber (e.g. {first_name.lower()}@{roll_no}).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = {
        "sub": student["user_id"],
        "student_id": student["student_id"],
        "roll_no": student["roll_no"],
        "full_name": student["full_name"],
        "programme_code": student["programme_code"]
    }

    token = create_access_token(token_payload)
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=86400,
        student_id=student["student_id"],
        roll_no=student["roll_no"],
        full_name=student["full_name"],
        programme_code=student["programme_code"]
    )

@router.get("/me", response_model=StudentProfile)
async def get_my_profile(current_student: dict = Depends(get_current_student)):
    session = DatabaseSession(student_id=current_student["student_id"], user_id=current_student["user_id"])
    profile = DataRepository.get_student_profile(session)
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return StudentProfile(**profile)
