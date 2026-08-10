from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey
)

from database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )


class Expense(Base):

    __tablename__ = "expenses"

    expense_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(100),
        nullable=False
    )

    category = Column(
        String(50),
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    payment_mode = Column(
        String(30),
        nullable=False
    )

    expense_date = Column(
        Date,
        nullable=False
    )

    # Expense belongs to the logged-in user
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )