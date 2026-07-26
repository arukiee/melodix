"""String manipulation helpers."""

def slugify(text: str) -> str:
    import re, unicodedata
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")
