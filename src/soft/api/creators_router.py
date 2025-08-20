from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..db import get_db
from ..models import Creator
from ..schemas import (
    CreatorCreate, CreatorResponse, CreatorUpdate, 
    CreatorBulkCreate, CreatorListResponse, ErrorResponse
)

router = APIRouter(
    prefix="/creators",
    tags=["creators"],
    responses={404: {"model": ErrorResponse}}
)

# Helper function to get creator by ID
def get_creator(db: Session, creator_id: str) -> Optional[Creator]:
    return db.query(Creator).filter(Creator.creator_id == creator_id).first()

@router.post(
    "", 
    response_model=CreatorResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Creator already exists"}
    }
)
def create_creator(creator: CreatorCreate, db: Session = Depends(get_db)):
    """
    Create a new creator.
    
    - **creator_id**: Unique identifier for the creator
    - **q**: Quality score between 0 and 1 (default: 0.5)
    - **hard_cap_eur**: Maximum payout in EUR (default: 50.0)
    """
    db_creator = get_creator(db, creator.creator_id)
    if db_creator:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Creator with id {creator.creator_id} already exists"
        )
    
    db_creator = Creator(
        creator_id=creator.creator_id,
        q=creator.q,
        hard_cap_eur=creator.hard_cap_eur,
        last_seen=int(datetime.utcnow().timestamp())
    )
    
    db.add(db_creator)
    db.commit()
    db.refresh(db_creator)
    return db_creator

@router.get(
    "/{creator_id}",
    response_model=CreatorResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Creator not found"}
    }
)
def read_creator(creator_id: str, db: Session = Depends(get_db)):
    """
    Get a creator by ID.
    
    Returns 404 if the creator is not found.
    """
    db_creator = get_creator(db, creator_id)
    if db_creator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with id {creator_id} not found"
        )
    return db_creator

@router.get(
    "", 
    response_model=CreatorListResponse,
    response_model_exclude_none=True
)
def list_creators(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    List all creators with pagination.
    
    - **skip**: Number of items to skip (for pagination)
    - **limit**: Maximum number of items to return (max 1000)
    """
    if limit > 1000:
        limit = 1000
        
    creators = db.query(Creator).offset(skip).limit(limit).all()
    total = db.query(Creator).count()
    
    return {"items": creators, "total": total}

@router.delete(
    "/{creator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Creator not found"}
    }
)
def delete_creator(creator_id: str, db: Session = Depends(get_db)):
    """
    Delete a creator by ID (soft delete).
    
    Returns 404 if the creator is not found.
    """
    db_creator = get_creator(db, creator_id)
    if db_creator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with id {creator_id} not found"
        )
    
    # Soft delete by setting last_seen to None
    db_creator.last_seen = None
    db.commit()
    return None

@router.post(
    "/init",
    status_code=status.HTTP_201_CREATED,
    response_model=List[CreatorResponse]
)
def init_creators(creators: CreatorBulkCreate, db: Session = Depends(get_db)):
    """
    Initialize multiple creators at once.
    
    Skips creators that already exist.
    """
    created_creators = []
    current_time = int(datetime.utcnow().timestamp())
    
    for creator in creators.creators:
        # Skip if creator already exists
        if get_creator(db, creator.creator_id):
            continue
            
        db_creator = Creator(
            creator_id=creator.creator_id,
            q=creator.q,
            hard_cap_eur=creator.hard_cap_eur,
            last_seen=current_time
        )
        db.add(db_creator)
        created_creators.append(db_creator)
    
    if created_creators:
        db.commit()
        for creator in created_creators:
            db.refresh(creator)
    
    return created_creators
