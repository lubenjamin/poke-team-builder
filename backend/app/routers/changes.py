from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import MoveChangeLog, PokemonChangeLog
from app.schemas.change_log import ChangeLogRead, MoveChangeLogRead

router = APIRouter(prefix="/api/changes", tags=["changes"])


@router.get("", response_model=list[ChangeLogRead])
def list_changes(
    limit: int = 100, db: Session = Depends(get_db)
) -> list[PokemonChangeLog]:
    stmt = select(PokemonChangeLog).order_by(PokemonChangeLog.detected_at.desc()).limit(limit)
    return list(db.scalars(stmt))


@router.get("/moves", response_model=list[MoveChangeLogRead])
def list_move_changes(
    limit: int = 100, db: Session = Depends(get_db)
) -> list[MoveChangeLog]:
    stmt = select(MoveChangeLog).order_by(MoveChangeLog.detected_at.desc()).limit(limit)
    return list(db.scalars(stmt))
