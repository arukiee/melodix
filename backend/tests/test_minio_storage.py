import io
import pytest
from app.storage.minio_service import StorageService

@pytest.fixture(scope="module")
def storage_service() -> StorageService:
    return StorageService()

def test_minio_crud_lifecycle(storage_service: StorageService):
    obj_name = "test_minio.txt"
    payload = b"hello minio"
    # Upload
    storage_service.upload(obj_name, io.BytesIO(payload), len(payload))
    # Download & verify
    downloaded = storage_service.download(obj_name)
    assert downloaded == payload
    # Delete
    storage_service.delete(obj_name)
    # Verify deletion raises error
    with pytest.raises(Exception):
        storage_service.download(obj_name)
