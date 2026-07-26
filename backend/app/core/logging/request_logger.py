from .logger import logger

def log_request(request):
    logger.info(f"{request.method} {request.url.path} - Remote: {request.client.host}")
