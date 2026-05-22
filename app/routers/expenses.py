from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseOut
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    dependencies=[Depends(get_current_user)],
)


async def _get_expense(expense_id, user: User, db: AsyncSession) -> Expense:
    """Get expense and verify ownership"""
    result = await db.execute(
        select(Expense).where(
            (Expense.id == expense_id) & (Expense.user_id == user.id)
        )
    )
    expense = result.scalars().first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    return expense


@router.get("", response_model=dict)
async def list_expenses(
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all expenses for current user"""
    query = select(Expense).where(Expense.user_id == user.id)

    if category:
        query = query.where(Expense.category == category)

    if date_from:
        query = query.where(Expense.expense_date >= date_from)

    if date_to:
        query = query.where(Expense.expense_date <= date_to)

    result = await db.execute(query)
    expenses = result.scalars().all()

    return {"data": [ExpenseOut.model_validate(e) for e in expenses], "meta": {"total": len(expenses)}}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_create: ExpenseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new expense"""
    new_expense = Expense(
        user_id=user.id,
        category=expense_create.category,
        amount=expense_create.amount,
        description=expense_create.description,
        expense_date=expense_create.expense_date,
    )

    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)

    return {"data": ExpenseOut.model_validate(new_expense)}


@router.get("/{expense_id}", response_model=dict)
async def get_expense(
    expense_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get expense details"""
    expense = await _get_expense(expense_id, user, db)
    return {"data": ExpenseOut.model_validate(expense)}


@router.put("/{expense_id}", response_model=dict)
async def update_expense(
    expense_id,
    expense_update: ExpenseUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an expense"""
    expense = await _get_expense(expense_id, user, db)

    update_data = expense_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)

    await db.commit()
    await db.refresh(expense)

    return {"data": ExpenseOut.model_validate(expense)}


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an expense"""
    expense = await _get_expense(expense_id, user, db)
    await db.delete(expense)
    await db.commit()
