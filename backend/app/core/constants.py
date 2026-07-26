"""Application‑wide constants."""

# API
API_VERSION = "v1"
DEFAULT_PAGINATION_SIZE = 20
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MiB

# Supported media formats
SUPPORTED_AUDIO_FORMATS = {"wav", "mp3", "flac"}
SUPPORTED_IMAGE_FORMATS = {"png", "jpg", "jpeg", "svg"}

# Caching
DEFAULT_CACHE_TTL = 300  # seconds

# Embedding dimensions (default for sentence‑transformer model)
DEFAULT_EMBEDDING_DIM = 384
