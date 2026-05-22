from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.models.user_setting import UserSetting
from app.schemas.settings import UserSettingsOut, UserSettingsUpdate
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)],
)

DEFAULT_CATEGORIES = "Вязаные игрушки плюш,Вязаные игрушки акрил,Лотерейные игрушки,Брелоки"


async def _get_or_create(user: User, db: AsyncSession) -> UserSetting:
    result = await db.execute(select(UserSetting).where(UserSetting.user_id == user.id))
    setting = result.scalars().first()
    if not setting:
        setting = UserSetting(user_id=user.id)
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
    return setting


def _to_out(s: UserSetting) -> UserSettingsOut:
    return UserSettingsOut(
        currency=s.currency,
        categories=[c.strip() for c in s.categories.split(",") if c.strip()],
        low_stock_threshold=s.low_stock_threshold,
    )


@router.get("", response_model=dict)
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    setting = await _get_or_create(user, db)
    return {"data": _to_out(setting)}


@router.put("", response_model=dict)
async def update_settings(
    body: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    setting = await _get_or_create(user, db)
    if body.currency is not None:
        setting.currency = body.currency
    if body.categories is not None:
        setting.categories = ",".join(body.categories)
    if body.low_stock_threshold is not None:
        setting.low_stock_threshold = body.low_stock_threshold
    await db.commit()
    await db.refresh(setting)
    return {"data": _to_out(setting)}
