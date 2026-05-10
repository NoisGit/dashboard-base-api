"""Supabase Storage URL service for Coredeck uploads."""

import uuid
from urllib.parse import urlparse

from src.api.error import InvalidContainerError, StorageServiceError
from src.config.config import settings

ALLOWED_CONTAINERS = [
    "access-logs",
    "companies",
    "documents",
    "location-logbook",
    "locations",
    "support-tickets",
]


class StorageService:
    """Generate deterministic Supabase Storage object URLs."""

    def __init__(self) -> None:
        self.supabase_url = (settings.SUPABASE_URL or "http://localhost:54321").rstrip("/")
        self.bucket = settings.SUPABASE_STORAGE_BUCKET.strip("/")

    def _validate_container(self, container_name: str) -> None:
        if container_name not in ALLOWED_CONTAINERS:
            raise InvalidContainerError("Invalid container name.")

    def _build_object_name(self, container_name: str, file_extension: str) -> str:
        normalized_extension = file_extension.strip().lstrip(".") or "bin"
        return f"{container_name}/{uuid.uuid4()}.{normalized_extension}"

    def _object_url(self, object_name: str) -> str:
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{object_name}"

    def generate_upload_url(
        self,
        container_name: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Generate a Supabase object URL for a new upload target."""
        self._validate_container(container_name)
        object_name = self._build_object_name(container_name, file_extension)
        return {
            "blob_url": self._object_url(object_name),
            "blob_name": object_name,
        }

    def generate_update_url(
        self,
        old_blob_url: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Generate replacement object metadata for a Supabase Storage object."""
        container_name, _ = self.extract_blob_info_from_url(old_blob_url)
        upload_payload = self.generate_upload_url(
            container_name=container_name,
            file_extension=file_extension,
            content_type=content_type,
        )
        return {
            "delete_url": old_blob_url,
            "new_blob_name": upload_payload["blob_name"],
            "new_blob_url": upload_payload["blob_url"],
        }

    def generate_delete_url(self, blob_url: str) -> dict:
        """Return the Supabase object URL that should be deleted."""
        return {"blob_url": blob_url}

    def generate_read_url(self, container_name: str, blob_name: str) -> str:
        """Generate a Supabase public read URL for an existing object."""
        self._validate_container(container_name)
        object_name = blob_name.strip("/")
        if not object_name.startswith(f"{container_name}/"):
            object_name = f"{container_name}/{object_name}"
        return self._object_url(object_name)

    def generate_upload_url(
        self,
        container_name: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Compatibility method for upload URL generation."""
        return self.generate_upload_url(container_name, file_extension, content_type)

    def generate_update_url(
        self,
        old_blob_url: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Compatibility method for update URL generation."""
        return self.generate_update_url(old_blob_url, file_extension, content_type)

    def generate_delete_url(self, blob_url: str) -> dict:
        """Compatibility method for delete URL generation."""
        return self.generate_delete_url(blob_url)

    def generate_read_url(self, container_name: str, blob_name: str) -> str:
        """Compatibility method for read URL generation."""
        return self.generate_read_url(container_name, blob_name)

    def extract_blob_info_from_url(self, blob_url: str) -> tuple[str, str]:
        """Extract the Coredeck container and object name from a storage URL."""
        try:
            parsed_url = urlparse(blob_url)
            marker = f"/storage/v1/object/public/{self.bucket}/"
            if marker in parsed_url.path:
                object_name = parsed_url.path.split(marker, 1)[1]
            else:
                object_name = parsed_url.path.strip("/").split("/", 1)[-1]

            path_parts = object_name.split("/", 1)
            if len(path_parts) < 2:
                raise ValueError("Invalid storage URL format")

            container_name = path_parts[0]
            self._validate_container(container_name)
            return container_name, path_parts[1]

        except Exception as exc:
            raise StorageServiceError("Failed to extract storage object info from URL.") from exc
