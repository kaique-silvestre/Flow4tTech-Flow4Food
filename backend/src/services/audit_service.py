import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.models.audit_logs import AuditLog


def log(
    db: Session,
    action: str,
    *,
    tenant_id: Optional[int] = None,  # noqa: UP045
    user_id: Optional[int] = None,  # noqa: UP045
    entity: Optional[str] = None,  # noqa: UP045
    entity_id: Optional[int] = None,  # noqa: UP045
    before: Optional[dict] = None,  # noqa: UP045
    after: Optional[dict] = None,  # noqa: UP045
    impersonated_by: Optional[int] = None,  # noqa: UP045
) -> None:
    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        before_data=json.dumps(before) if before else None,
        after_data=json.dumps(after) if after else None,
        impersonated_by=impersonated_by,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()


def log_background(
    action: str,
    *,
    tenant_id: Optional[int] = None,  # noqa: UP045
    user_id: Optional[int] = None,  # noqa: UP045
    entity: Optional[str] = None,  # noqa: UP045
    entity_id: Optional[int] = None,  # noqa: UP045
    before: Optional[dict] = None,  # noqa: UP045
    after: Optional[dict] = None,  # noqa: UP045
    impersonated_by: Optional[int] = None,  # noqa: UP045
) -> None:
    from src.core.database import PlatformSessionLocal

    db = PlatformSessionLocal()
    try:
        log(
            db,
            action,
            tenant_id=tenant_id,
            user_id=user_id,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            impersonated_by=impersonated_by,
        )
    except Exception:
        pass
    finally:
        db.close()
