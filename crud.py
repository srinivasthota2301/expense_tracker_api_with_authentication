from sqlalchemy.orm import Session

from sqlalchemy import func

from models import Expense, User

from schemas import ExpenseCreate, ExpenseUpdate

from auth import (
    hash_password,
    verify_password
)


# =====================================================
# EXPENSE CRUD
# =====================================================

def create_expense(
    db: Session,
    expense: ExpenseCreate,
    user_id: int
):

    new_expense = Expense(
        **expense.model_dump(),
        user_id=user_id
    )

    db.add(new_expense)

    db.commit()

    db.refresh(new_expense)

    return new_expense


def get_all_expenses(
    db: Session,
    user_id: int
):

    return db.query(
        Expense
    ).filter(
        Expense.user_id == user_id
    ).all()


def get_expense_by_id(
    db: Session,
    expense_id: int,
    user_id: int
):

    return db.query(
        Expense
    ).filter(
        Expense.expense_id == expense_id,
        Expense.user_id == user_id
    ).first()


def update_expense(
    db: Session,
    expense_id: int,
    expense: ExpenseCreate,
    user_id: int
):

    db_expense = get_expense_by_id(
        db,
        expense_id,
        user_id
    )

    if db_expense:

        db_expense.title = expense.title

        db_expense.category = expense.category

        db_expense.amount = expense.amount

        db_expense.payment_mode = expense.payment_mode

        db_expense.expense_date = expense.expense_date

        db.commit()

        db.refresh(db_expense)

    return db_expense


def patch_expense(
    db: Session,
    expense_id: int,
    expense: ExpenseUpdate,
    user_id: int
):

    db_expense = get_expense_by_id(
        db,
        expense_id,
        user_id
    )

    if db_expense:

        update_data = expense.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():

            setattr(
                db_expense,
                key,
                value
            )

        db.commit()

        db.refresh(db_expense)

    return db_expense


def delete_expense(
    db: Session,
    expense_id: int,
    user_id: int
):

    db_expense = get_expense_by_id(
        db,
        expense_id,
        user_id
    )

    if db_expense:

        db.delete(db_expense)

        db.commit()

    return db_expense


def get_category(
    db: Session,
    category: str,
    user_id: int
):

    return db.query(
        Expense
    ).filter(
        Expense.category == category,
        Expense.user_id == user_id
    ).all()


def total_expense(
    db: Session,
    user_id: int
):

    return db.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id
    ).scalar()


def highest_expense(
    db: Session,
    user_id: int
):

    return db.query(
        Expense
    ).filter(
        Expense.user_id == user_id
    ).order_by(
        Expense.amount.desc()
    ).first()


# =====================================================
# USER CRUD
# =====================================================

def create_user(
    db: Session,
    username: str,
    email: str,
    password: str
):

    hashed_password = hash_password(
        password
    )

    user = User(
        username=username,
        email=email,
        password_hash=hashed_password
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user


def get_user_by_username(
    db: Session,
    username: str
):

    return db.query(
        User
    ).filter(
        User.username == username
    ).first()


def get_user_by_email(
    db: Session,
    email: str
):

    return db.query(
        User
    ).filter(
        User.email == email
    ).first()


def authenticate_user(
    db: Session,
    username: str,
    password: str
):

    user = get_user_by_username(
        db,
        username
    )

    if not user:

        return None

    if not verify_password(
        password,
        user.password_hash
    ):

        return None

    return user


def get_user_by_id(
    db: Session,
    user_id: int
):

    return db.query(
        User
    ).filter(
        User.id == user_id
    ).first()


def reset_password(
    db: Session,
    user_id: int,
    new_password: str
):

    user = get_user_by_id(
        db,
        user_id
    )

    if not user:

        return None

    user.password_hash = hash_password(
        new_password
    )

    db.commit()

    db.refresh(user)

    return user