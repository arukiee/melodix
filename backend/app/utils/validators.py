"""Common validation utilities."""

def validate_file_extension(filename: str, allowed: set[str]) -> bool:
    return filename.split('.')[-1].lower() in allowed
