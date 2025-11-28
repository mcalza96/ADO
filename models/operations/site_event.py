from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class SiteEvent:
    id: Optional[int]
    site_id: int
    event_type: str  # e.g., 'Preparation', 'VectorControl', 'Incorporation'
    event_date: datetime
    description: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
