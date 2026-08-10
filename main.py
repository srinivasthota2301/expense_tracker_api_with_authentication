from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    Response
)

from fastapi.staticfiles import StaticFiles

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from slowapi import Limiter, _rate_limit_exceeded_handler

from slowapi.util import get_remote_address

from slowapi.errors import RateLimitExceeded

import models

import schemas

import crud

from database import (
    engine,
    get_db,
    Base
)

from jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    create_reset_token,
    verify_reset_token
)

from dependencies import get_current_user


# =====================================================
# CREATE TABLES
# =====================================================

Base.metadata.create_all(
    bind=engine
)


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Expense Tracker API"
)


# =====================================================
# RATE LIMITING
# =====================================================
# Applied to /login and /register so nothing can brute-force
# passwords or spam-create accounts. Keyed by client IP.

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# Serve the login page's CSS/JS assets
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# =====================================================
# HOME -> LOGIN PAGE
# =====================================================

@app.get("/")
def home():

    return FileResponse("static/login.html")


# =====================================================
# REGISTER
# =====================================================

@app.post("/register")
@limiter.limit("5/minute")
def register(
    request: Request,
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = crud.get_user_by_username(
        db,
        user.username
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )


    existing_email = crud.get_user_by_email(
        db,
        user.email
    )

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )


    new_user = crud.create_user(
        db,
        user.username,
        user.email,
        user.password
    )


    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


# =====================================================
# LOGIN
# =====================================================

@app.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    user: schemas.UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):

    authenticated_user = crud.authenticate_user(
        db,
        user.username,
        user.password
    )

    if not authenticated_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )


    token_data = {
        "sub": str(
            authenticated_user.id
        )
    }

    access_token = create_access_token(
        data=token_data
    )

    refresh_token = create_refresh_token(
        data=token_data
    )


    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 60
    )

    # Scoped to /refresh so this cookie is never sent on ordinary
    # /expenses-style requests — it only leaves the browser when the
    # client is specifically asking to refresh the access token.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/refresh"
    )


    return {
        "message": "Login successful"
    }


# =====================================================
# REFRESH
# =====================================================

@app.post("/refresh")
def refresh(
    request: Request,
    response: Response
):

    token = request.cookies.get(
        "refresh_token"
    )

    if not token:

        raise HTTPException(
            status_code=401,
            detail="Refresh token missing, please log in again"
        )


    payload = verify_refresh_token(
        token
    )

    if payload is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token, please log in again"
        )


    user_id = payload.get("sub")

    if user_id is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token payload"
        )


    # Issue a fresh access token. The refresh token itself is left as-is
    # (rotate-on-use + a server-side revocation list is the next step up
    # in security if you want to invalidate stolen refresh tokens early).
    new_access_token = create_access_token(
        data={"sub": user_id}
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 60
    )

    return {
        "message": "Access token refreshed"
    }


# =====================================================
# LOGOUT
# =====================================================

@app.post("/logout")
def logout(
    response: Response
):

    response.delete_cookie(
        key="access_token"
    )

    response.delete_cookie(
        key="refresh_token",
        path="/refresh"
    )

    return {
        "message": "Logout successful"
    }


# =====================================================
# FORGOT PASSWORD
# =====================================================
# No email service is wired up yet, so this returns the reset token
# directly in the response so the flow is testable end to end. Before
# this goes anywhere near production: stop returning the token here,
# and instead email a link like https://yourapp.com/reset?token=...
# through a real mail provider (SES, Postmark, SendGrid, etc).

@app.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    payload: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = crud.get_user_by_email(
        db,
        payload.email
    )

    # Always return the same generic message whether or not the email
    # exists — confirming/denying an email's existence is itself a
    # privacy leak (account enumeration).
    generic_response = {
        "message": "If that email is registered, a reset link has been generated."
    }

    if not user:

        return generic_response

    reset_token = create_reset_token(
        data={
            "sub": str(user.id)
        }
    )

    # DEV-MODE ONLY: exposing the token here so you can test without an
    # email provider. Remove "reset_token" from this response once real
    # email sending is wired up.
    generic_response["reset_token"] = reset_token

    return generic_response


# =====================================================
# RESET PASSWORD
# =====================================================

@app.post("/reset-password")
@limiter.limit("5/minute")
def reset_password_endpoint(
    request: Request,
    payload: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    token_payload = verify_reset_token(
        payload.token
    )

    if token_payload is None:

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )


    user_id = token_payload.get("sub")

    if user_id is None:

        raise HTTPException(
            status_code=400,
            detail="Invalid reset token payload"
        )


    if len(payload.new_password) < 8:

        raise HTTPException(
            status_code=400,
            detail="Password needs to be at least 8 characters"
        )


    updated_user = crud.reset_password(
        db,
        int(user_id),
        payload.new_password
    )

    if not updated_user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    return {
        "message": "Password has been reset. You can log in with your new password now."
    }


# =====================================================
# CREATE EXPENSE
# =====================================================

@app.post(
    "/expenses",
    response_model=schemas.ExpenseResponse
)
def create(
    expense: schemas.ExpenseCreate,

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    return crud.create_expense(
        db,
        expense,
        current_user
    )


# =====================================================
# GET ALL EXPENSES
# =====================================================

@app.get(
    "/expenses",
    response_model=list[
        schemas.ExpenseResponse
    ]
)
def all_expenses(

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    return crud.get_all_expenses(
        db,
        current_user
    )


# =====================================================
# GET EXPENSE BY ID
# =====================================================

@app.get(
    "/expenses/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def expense(

    expense_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    data = crud.get_expense_by_id(
        db,
        expense_id,
        current_user
    )

    if not data:

        raise HTTPException(
            status_code=404,
            detail="Expense Not Found"
        )

    return data


# =====================================================
# UPDATE EXPENSE
# =====================================================

@app.put(
    "/expenses/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def update(

    expense_id: int,

    expense: schemas.ExpenseCreate,

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    data = crud.update_expense(
        db,
        expense_id,
        expense,
        current_user
    )

    if not data:

        raise HTTPException(
            status_code=404,
            detail="Expense Not Found"
        )

    return data


# =====================================================
# PATCH EXPENSE
# =====================================================

@app.patch(
    "/expenses/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def patch(

    expense_id: int,

    expense: schemas.ExpenseUpdate,

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    data = crud.patch_expense(
        db,
        expense_id,
        expense,
        current_user
    )

    if not data:

        raise HTTPException(
            status_code=404,
            detail="Expense Not Found"
        )

    return data


# =====================================================
# DELETE EXPENSE
# =====================================================

@app.delete(
    "/expenses/{expense_id}"
)
def delete(

    expense_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    data = crud.delete_expense(
        db,
        expense_id,
        current_user
    )

    if not data:

        raise HTTPException(
            status_code=404,
            detail="Expense Not Found"
        )

    return {
        "message": "Expense Deleted Successfully"
    }


# =====================================================
# CATEGORY
# =====================================================

@app.get(
    "/category/{category}",
    response_model=list[
        schemas.ExpenseResponse
    ]
)
def category(

    category: str,

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    return crud.get_category(
        db,
        category,
        current_user
    )


# =====================================================
# TOTAL
# =====================================================

@app.get("/total")
def total(

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    return {
        "Total Expense": crud.total_expense(
            db,
            current_user
        )
    }


# =====================================================
# HIGHEST
# =====================================================

@app.get(
    "/highest",
    response_model=schemas.ExpenseResponse
)
def highest(

    db: Session = Depends(
        get_db
    ),

    current_user: int = Depends(
        get_current_user
    )
):

    data = crud.highest_expense(
        db,
        current_user
    )

    if not data:

        raise HTTPException(
            status_code=404,
            detail="No Expenses Found"
        )

    return data