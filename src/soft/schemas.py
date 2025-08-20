from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Enums
class CreatorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# Base schemas
class CreatorBase(BaseModel):
    creator_id: str = Field(..., description="Unique identifier for the creator")
    q: float = Field(0.5, ge=0.0, le=1.0, description="Quality score between 0 and 1")
    hard_cap_eur: float = Field(50.0, gt=0, description="Maximum payout in EUR")
    status: Optional[CreatorStatus] = Field(CreatorStatus.ACTIVE, description="Creator status")

# Request schemas
class CreatorCreate(CreatorBase):
    pass

class CreatorUpdate(BaseModel):
    q: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score between 0 and 1")
    hard_cap_eur: Optional[float] = Field(None, gt=0, description="Maximum payout in EUR")
    status: Optional[CreatorStatus] = Field(None, description="Creator status")

class CreatorBulkCreate(BaseModel):
    creators: List[CreatorCreate] = Field(..., description="List of creators to create")

# Response schemas
class CreatorResponse(CreatorBase):
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "creator_id": "creator123",
                "q": 0.7,
                "hard_cap_eur": 50.0,
                "status": "active",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

class CreatorListResponse(BaseModel):
    items: List[CreatorResponse] = Field(..., description="List of creators")
    total: int = Field(..., description="Total number of creators")

# Error schemas
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {
            "example": {"detail": "Creator not found"}
        }
