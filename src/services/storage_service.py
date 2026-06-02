"""Storage URL service for Coredeck uploads."""

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
    """Generate deterministic public storage object URLs."""

    def __init__(self) -> None:
        self.storage_base_url = settings.storage_base_url.rstrip("/")
        self.bucket = settings.storage_bucket.strip("/")

    def _validate_container(self, container_name: str) -> None:
        if container_name not in ALLOWED_CONTAINERS:
            raise InvalidContainerError("Invalid container name.")

    def _build_object_name(self, container_name: str, file_extension: str) -> str:
        normalized_extension = file_extension.strip().lstrip(".") or "bin"
        return f"{container_name}/{uuid.uuid4()}.{normalized_extension}"

    def _object_url(self, object_name: str) -> str:
        return f"{self.storage_base_url}/{object_name.strip('/')}"

    def generate_upload_url(
        self,
        container_name: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Generate an object URL for a new upload target."""
        self._validate_container(container_name)
        object_name = self._build_object_name(container_name, file_extension)
        return {
            "object_url": self._object_url(object_name),
            "object_name": object_name,
        }

    def generate_update_url(
        self,
        old_object_url: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Generate replacement object metadata for a storage object."""
        container_name, _ = self.extract_object_info_from_url(old_object_url)
        upload_payload = self.generate_upload_url(
            container_name=container_name,
            file_extension=file_extension,
            content_type=content_type,
        )
        return {
            "delete_url": old_object_url,
            "new_object_name": upload_payload["object_name"],
            "new_object_url": upload_payload["object_url"],
        }

    def generate_delete_url(self, object_url: str) -> dict:
        """Return the storage object URL that should be deleted."""
        return {"object_url": object_url}

    def generate_read_url(self, container_name: str, object_name: str) -> str:
        """Generate a public read URL for an existing object."""
        self._validate_container(container_name)
        normalized_object_name = object_name.strip("/")
        if not normalized_object_name.startswith(f"{container_name}/"):
            normalized_object_name = f"{container_name}/{normalized_object_name}"
        return self._object_url(normalized_object_name)

    def extract_object_info_from_url(self, object_url: str) -> tuple[str, str]:
        """Extract the Coredeck container and object name from a storage URL."""
        try:
            parsed_url = urlparse(object_url)
            base_path = urlparse(self.storage_base_url).path.strip("/")
            full_path = parsed_url.path.strip("/")

            if base_path and full_path.startswith(f"{base_path}/"):
                object_name = full_path[len(base_path) + 1:]
            else:
                marker = f"/storage/v1/object/public/{self.bucket}/"
                if marker in parsed_url.path:
                    object_name = parsed_url.path.split(marker, 1)[1]
                else:
                    object_name = full_path.split("/", 1)[-1]

            path_parts = object_name.split("/", 1)
            if len(path_parts) < 2:
                raise ValueError("Invalid storage URL format")

            container_name = path_parts[0]
            self._validate_container(container_name)
            return container_name, path_parts[1]

        except Exception as exc:
            raise StorageServiceError("Failed to extract storage object info from URL.") from exc
