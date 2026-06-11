"""Storage URL service for public assets and private tenant documents."""

import mimetypes
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import jwt

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
ALLOWED_UPLOAD_TYPES = {
    "companies": {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    },
    "locations": {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    },
    "documents": {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    },
    "access-logs": {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    },
    "location-logbook": {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "mp4": "video/mp4",
    },
    "support-tickets": {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "pdf": "application/pdf",
    },
}
DOCUMENT_MAX_SIZE_BYTES = 10 * 1024 * 1024


class StorageService:
    """Manage public asset URLs and signed private document operations."""

    def __init__(self) -> None:
        self.storage_base_url = settings.storage_base_url.rstrip("/")
        self.bucket = settings.storage_bucket.strip("/")
        self.backend_base_url = settings.backend_public_base_url.rstrip("/")
        self.private_root = Path(settings.private_storage_root).resolve()
        self.signed_url_expire_seconds = settings.storage_signed_url_expire_seconds

    def _validate_container(self, container_name: str) -> None:
        if container_name not in ALLOWED_CONTAINERS:
            raise InvalidContainerError("Invalid container name.")

    def _build_object_name(self, container_name: str, file_extension: str) -> str:
        normalized_extension = file_extension.strip().lower().lstrip(".")
        return f"{container_name}/{uuid.uuid4()}.{normalized_extension}"

    def _validate_upload_type(
        self,
        container_name: str,
        file_extension: str,
        content_type: str,
    ) -> str:
        normalized_extension = file_extension.strip().lower().lstrip(".")
        normalized_content_type = content_type.strip().lower()
        expected_content_type = ALLOWED_UPLOAD_TYPES[container_name].get(
            normalized_extension
        )
        if not expected_content_type or expected_content_type != normalized_content_type:
            raise StorageServiceError(
                "File extension and content type are not allowed for this container."
            )
        return normalized_extension

    def _object_url(self, object_name: str) -> str:
        return f"{self.storage_base_url}/{object_name.strip('/')}"

    def _encode_storage_token(self, claims: dict, expires_at: datetime) -> str:
        payload = {
            **claims,
            "exp": expires_at,
            "iat": datetime.now(timezone.utc),
            "jti": uuid.uuid4().hex,
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    def _decode_storage_token(self, token: str, expected_type: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise StorageServiceError("The signed storage URL has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise StorageServiceError("Invalid signed storage URL.") from exc

        if payload.get("type") != expected_type:
            raise StorageServiceError("Invalid signed storage operation.")
        return payload

    def _private_object_path(self, object_name: str) -> Path:
        normalized = object_name.strip("/")
        target = (self.private_root / normalized).resolve()
        if self.private_root != target and self.private_root not in target.parents:
            raise StorageServiceError("Invalid private object name.")
        return target

    def _validate_document_object_name(
        self,
        object_name: str,
        company_id: int,
    ) -> None:
        prefix = f"documents/company-{company_id}/"
        normalized = object_name.strip("/")
        if not normalized.startswith(prefix) or ".." in Path(normalized).parts:
            raise StorageServiceError(
                "Document object does not belong to the requested company."
            )

    def generate_upload_url(
        self,
        container_name: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Generate a public object URL for non-sensitive assets."""
        self._validate_container(container_name)
        self._validate_upload_type(container_name, file_extension, content_type)
        if container_name == "documents":
            raise StorageServiceError(
                "Documents require a tenant-bound private upload intent."
            )
        object_name = self._build_object_name(container_name, file_extension)
        return {
            "object_url": self._object_url(object_name),
            "object_name": object_name,
        }

    def generate_document_upload_intent(
        self,
        company_id: int,
        file_name: str,
        content_type: str,
        size_bytes: int,
    ) -> dict:
        """Generate a short-lived upload URL bound to one company."""
        extension = Path(file_name).suffix
        normalized_extension = self._validate_upload_type(
            "documents",
            extension,
            content_type,
        )
        if size_bytes <= 0 or size_bytes > DOCUMENT_MAX_SIZE_BYTES:
            raise StorageServiceError("Document size is outside the allowed limit.")

        object_name = (
            f"documents/company-{company_id}/"
            f"{uuid.uuid4().hex}.{normalized_extension}"
        )
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.signed_url_expire_seconds
        )
        token = self._encode_storage_token(
            {
                "type": "storage_upload",
                "company_id": company_id,
                "object_name": object_name,
                "content_type": content_type.strip().lower(),
                "size_bytes": size_bytes,
            },
            expires_at,
        )
        return {
            "upload_url": (
                f"{self.backend_base_url}/api/v1/storage/private/upload/{token}"
            ),
            "object_name": object_name,
            "expires_at": expires_at,
        }

    def store_private_upload(
        self,
        token: str,
        content: bytes,
        content_type: str,
    ) -> str:
        """Verify an upload signature and atomically store its bytes."""
        payload = self._decode_storage_token(token, "storage_upload")
        object_name = str(payload.get("object_name", ""))
        company_id = int(payload.get("company_id", 0))
        expected_content_type = str(payload.get("content_type", "")).lower()
        expected_size = int(payload.get("size_bytes", 0))
        self._validate_document_object_name(object_name, company_id)

        if content_type.strip().lower() != expected_content_type:
            raise StorageServiceError("Uploaded content type does not match the intent.")
        if len(content) != expected_size or len(content) > DOCUMENT_MAX_SIZE_BYTES:
            raise StorageServiceError("Uploaded document size does not match the intent.")

        target = self._private_object_path(object_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f"{target.suffix}.tmp-{uuid.uuid4().hex}")
        temporary.write_bytes(content)
        temporary.replace(target)
        return object_name

    def ensure_private_document_exists(
        self,
        object_name: str,
        company_id: int,
    ) -> None:
        """Ensure metadata references an uploaded object owned by the company."""
        self._validate_document_object_name(object_name, company_id)
        if not self._private_object_path(object_name).is_file():
            raise StorageServiceError("Private document object was not uploaded.")

    def generate_private_read_url(
        self,
        object_name: str,
        company_id: int,
        file_name: str,
        content_type: str | None,
    ) -> str:
        """Generate a short-lived read URL for an authorized document."""
        self.ensure_private_document_exists(object_name, company_id)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.signed_url_expire_seconds
        )
        token = self._encode_storage_token(
            {
                "type": "storage_read",
                "company_id": company_id,
                "object_name": object_name,
                "file_name": Path(file_name).name,
                "content_type": content_type
                or mimetypes.guess_type(file_name)[0]
                or "application/octet-stream",
            },
            expires_at,
        )
        return f"{self.backend_base_url}/api/v1/storage/private/read/{token}"

    def resolve_private_read(self, token: str) -> tuple[Path, str, str]:
        """Resolve a signed read token to a private file response."""
        payload = self._decode_storage_token(token, "storage_read")
        object_name = str(payload.get("object_name", ""))
        company_id = int(payload.get("company_id", 0))
        self._validate_document_object_name(object_name, company_id)
        target = self._private_object_path(object_name)
        if not target.is_file():
            raise StorageServiceError("Private document object was not found.")
        return (
            target,
            Path(str(payload.get("file_name", target.name))).name,
            str(payload.get("content_type", "application/octet-stream")),
        )

    def delete_private_document(self, object_name: str, company_id: int) -> None:
        """Delete a private document using trusted server-side authorization."""
        self._validate_document_object_name(object_name, company_id)
        target = self._private_object_path(object_name)
        if target.is_file():
            target.unlink()

    def generate_update_url(
        self,
        old_object_url: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Generate replacement metadata for a public storage object."""
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
        """Return the public storage object URL that should be deleted."""
        return {"object_url": object_url}

    def generate_read_url(self, container_name: str, object_name: str) -> str:
        """Generate a public read URL for a non-sensitive object."""
        self._validate_container(container_name)
        if container_name == "documents":
            raise StorageServiceError(
                "Documents require an authorized signed read URL."
            )
        normalized_object_name = object_name.strip("/")
        if not normalized_object_name.startswith(f"{container_name}/"):
            normalized_object_name = f"{container_name}/{normalized_object_name}"
        return self._object_url(normalized_object_name)

    def extract_object_info_from_url(self, object_url: str) -> tuple[str, str]:
        """Extract the Locentr container and object name from a public URL."""
        try:
            parsed_url = urlparse(object_url)
            parsed_base = urlparse(self.storage_base_url)
            if (
                parsed_url.scheme not in {"http", "https"}
                or parsed_url.scheme != parsed_base.scheme
                or parsed_url.netloc != parsed_base.netloc
            ):
                raise ValueError("Storage URL does not belong to Locentr")

            base_path = parsed_base.path.strip("/")
            full_path = parsed_url.path.strip("/")

            if base_path and full_path.startswith(f"{base_path}/"):
                object_name = full_path[len(base_path) + 1:]
            else:
                raise ValueError("Storage URL path is outside the configured bucket")

            path_parts = object_name.split("/", 1)
            if len(path_parts) < 2:
                raise ValueError("Invalid storage URL format")

            container_name = path_parts[0]
            self._validate_container(container_name)
            return container_name, path_parts[1]

        except Exception as exc:
            raise StorageServiceError(
                "Failed to extract storage object info from URL."
            ) from exc
