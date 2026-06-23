from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.models.tenant_features import TenantFeature

router = APIRouter()


class FeatureItem(BaseModel):
    feature: str
    enabled: bool


@router.get("/features", response_model=list[FeatureItem], tags=["features"])
def get_app_features(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FeatureItem]:
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        return []
    rows = db.execute(
        select(TenantFeature).where(TenantFeature.tenant_id == tenant_id)
    ).scalars().all()
    return [FeatureItem(feature=r.feature, enabled=r.enabled) for r in rows]
