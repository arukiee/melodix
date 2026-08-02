"""MinIO storage service abstraction.

Provides a thin wrapper around the official ``minio`` Python client to
handle bucket creation and basic CRUD operations needed by the application.

The class is deliberately lightweight – it is instantiated lazily during
FastAPI startup (see ``backend/app/factory.py``) and does not keep any state
beyond the underlying ``Minio`` client instance.
"""

from __future__ import annotations

import logging
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error
from pydantic import ValidationError

from ..config.minio import MinIOSettings


class StorageService:
    """Simple wrapper around MinIO client.

    The service ensures the configured bucket exists on instantiation and
    exposes ``upload``, ``download`` and ``delete`` methods used by the test
    suite and the application code.
    """

    def __init__(self) -> None:
        try:
            self.settings = MinIOSettings()
        except ValidationError as exc:
            logging.error("Invalid MinIO settings: %s", exc)
            raise

        # Initialise MinIO client
        self.client = Minio(
            endpoint=self.settings.endpoint.replace("http://", "").replace("https://", ""),
            access_key=self.settings.access_key,
            secret_key=self.settings.secret_key,
            secure=self.settings.secure,
        )

        # Ensure bucket exists – create if missing
        try:
            if not self.client.bucket_exists(self.settings.bucket_name):
                self.client.make_bucket(self.settings.bucket_name)
                logging.info("Created MinIO bucket %s", self.settings.bucket_name)
            else:
                logging.debug("MinIO bucket %s already exists", self.settings.bucket_name)
        except S3Error as exc:
            logging.error("Failed to ensure MinIO bucket %s: %s", self.settings.bucket_name, exc)
            raise

    def _object_path(self, object_name: str) -> str:
        """Return the full object path within the bucket.

        Currently we store objects directly under the bucket without any
        sub‑folders, but this helper keeps the API flexible for future
        extensions.
        """
        return object_name

    def upload(self, object_name: str, data: BinaryIO, size: int) -> None:
        """Upload ``data`` to ``object_name``.

        Args:
            object_name: Name of the object in the bucket.
            data: A binary stream (e.g. ``io.BytesIO``).
            size: Size of the data in bytes.
        """
        try:
            self.client.put_object(
                bucket_name=self.settings.bucket_name,
                object_name=self._object_path(object_name),
                data=data,
                length=size,
                content_type="application/octet-stream",
            )
            logging.info("Uploaded object %s to bucket %s", object_name, self.settings.bucket_name)
        except S3Error as exc:
            logging.error("MinIO upload failed for %s: %s", object_name, exc)
            raise

    def download(self, object_name: str) -> bytes:
        """Download the object and return its bytes.

        Raises:
            Exception: If the object does not exist or a network error occurs.
        """
        try:
            response = self.client.get_object(
                bucket_name=self.settings.bucket_name,
                object_name=self._object_path(object_name),
            )
            data = response.read()
            response.close()
            response.release_conn()
            logging.info("Downloaded object %s from bucket %s", object_name, self.settings.bucket_name)
            return data
        except S3Error as exc:
            logging.error("MinIO download failed for %s: %s", object_name, exc)
            raise

    def delete(self, object_name: str) -> None:
        """Delete the specified object.

        If the object does not exist ``minio`` raises ``S3Error``; we let the
        exception propagate so callers can handle it as appropriate.
        """
        try:
            self.client.remove_object(
                bucket_name=self.settings.bucket_name,
                object_name=self._object_path(object_name),
            )
            logging.info("Deleted object %s from bucket %s", object_name, self.settings.bucket_name)
        except S3Error as exc:
            logging.error("MinIO delete failed for %s: %s", object_name, exc)
            raise
