from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.auth import ConfigSeguranca


def get_config(db: Session) -> Optional[ConfigSeguranca]:
    return db.execute(select(ConfigSeguranca).limit(1)).scalar_one_or_none()


def upsert_config(db: Session, senha_hash: str) -> ConfigSeguranca:
    config = get_config(db)
    if config is None:
        config = ConfigSeguranca(senha_hash=senha_hash)
        db.add(config)
    else:
        config.senha_hash = senha_hash
    db.commit()
    db.refresh(config)
    return config
