from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_internal_secret

router = APIRouter(prefix="/api/internal", tags=["internal"])

# Calls into jobs/scan_for_changes.py once the ingestion pipeline
# (services/pokeapi_client.py, validation.py, ingestion.py, change_detection.py) exists.


@router.post("/scan-for-changes", dependencies=[Depends(require_internal_secret)])
def scan_for_changes() -> None:
    raise HTTPException(status_code=501, detail="Change-scan pipeline is not yet implemented")
