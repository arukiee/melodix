"""Simple pagination helper."""

def paginate(items: list, page: int = 1, size: int = 20) -> dict:
    start = (page - 1) * size
    end = start + size
    return {
        "total": len(items),
        "page": page,
        "size": size,
        "results": items[start:end],
    }
