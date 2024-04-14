

import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class AltData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    last_updated: datetime.datetime = Field(index=True)
    altitude: float

class AltHealthData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    orbital_decay_timestamp: datetime.datetime = Field(index=True)
    orbit_sustained_timestamp: Optional[datetime.datetime] = Field(default=None)

