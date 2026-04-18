from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.system_setting import SystemSetting
from app.schemas.system_setting import SiteSettingsResponse, SiteSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SiteSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    from app.core.config import settings as core_settings
    
    # Return as dict
    settings_dict = {s.key: s.value for s in settings}
    if "SALES_PERSON_NUMBER" not in settings_dict:
        settings_dict["SALES_PERSON_NUMBER"] = core_settings.SALES_PERSON_NUMBER or "+8801798760871"
        
    return SiteSettingsResponse(settings=settings_dict)

@router.post("", response_model=SiteSettingsResponse)
async def update_settings(payload: SiteSettingsUpdate, db: AsyncSession = Depends(get_db)):
    # Upsert logic
    for key, value in payload.settings.items():
        # Find existing
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = str(value)
        else:
            new_setting = SystemSetting(key=key, value=str(value))
            db.add(new_setting)
            
    await db.commit()
    
    # Return updated list
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    settings_dict = {s.key: s.value for s in settings}
    return SiteSettingsResponse(settings=settings_dict)
