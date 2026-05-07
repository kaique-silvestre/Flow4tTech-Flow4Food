import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration


def init_sentry(dsn: str, env: str = "dev") -> None:
    """Initialize Sentry. No-op when DSN is empty (dev default)."""
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1 if env == "prod" else 1.0,
        send_default_pii=False,
    )
