import time
import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("melodix.access")

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        response = await call_next(request)
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_payload = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        logger.info(json.dumps(log_payload))
        return response
