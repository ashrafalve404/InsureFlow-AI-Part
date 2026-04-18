from pydantic import BaseModel
from typing import Dict, Any

class SiteSettingsUpdate(BaseModel):
    settings: Dict[str, str]

class SiteSettingsResponse(BaseModel):
    settings: Dict[str, str]
