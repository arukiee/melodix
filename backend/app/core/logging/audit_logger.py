from .logger import logger

def log_audit(event: str, user_id: str | None = None, details: dict | None = None):
    msg = f"AUDIT - event={event}"
    if user_id:
        msg += f" user_id={user_id}"
    if details:
        msg += f" details={details}"
    logger.info(msg)
