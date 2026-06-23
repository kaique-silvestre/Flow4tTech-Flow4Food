from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import get_settings

# Rate limiting is disabled under the test environment so the suite can issue
# many requests (e.g. repeated logins) without tripping the limiter.
limiter = Limiter(key_func=get_remote_address, enabled=get_settings().ENV != "test")
