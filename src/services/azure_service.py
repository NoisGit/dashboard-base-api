"""Service for interacting with Azure Blob Storage."""
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions,
    ContentSettings
)

from src.api.error import (
    InvalidContainerError,
    AzureServiceError
)
from src.config.config import settings

ALLOWED_CONTAINERS = [
    "access-logs",
    "documents",
    "location-logbook",
    "support-tickets",
]

BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(
    settings.AZURE_STORAGE_CONNECTION_STRING
)

if not BLOB_SERVICE_CLIENT:
    raise RuntimeError(
        "Failed to create BlobServiceClient with the provided connection string."
    )

ACCOUNT_NAME = BLOB_SERVICE_CLIENT.account_name


class AzureService:
    """
    AzureService provides methods to interact with Azure Blob Storage, including
    generating SAS upload URLs.
    """

    def __init__(self):
        pass

    def generate_sas_upload_url(
        self,
        container_name: str,
        file_extension: str,
        content_type: str
    ) -> dict:
        """
        Generates a SAS (Shared Access Signature) upload URL for a blob in the
        specified Azure Blob Storage container.
        """
        if container_name not in ALLOWED_CONTAINERS:
            raise InvalidContainerError("Invalid container name.")

        blob_name = f"{uuid.uuid4()}.{file_extension}"

        try:
            sas_token = generate_blob_sas(
                account_name=ACCOUNT_NAME,
                container_name=container_name,
                blob_name=blob_name,
                account_key=BLOB_SERVICE_CLIENT.credential.account_key,
                permission=BlobSasPermissions(write=True, create=True),
                expiry=datetime.now(timezone.utc) + timedelta(minutes=15),
                content_settings=ContentSettings(content_type=content_type)
            )

            upload_url = (
                f"https://{ACCOUNT_NAME}.blob.core.windows.net/"
                f"{container_name}/{blob_name}?{sas_token}"
            )

            return {
                "blob_url": upload_url,
                "blob_name": blob_name
            }

        except Exception as e:
            raise AzureServiceError("Failed to generate upload URL.") from e

    def generate_sas_update_url(
        self,
        old_blob_url: str,
        file_extension: str,
        content_type: str
    ) -> dict:
        """
        Generates a SAS URL for updating a blob in the specified container.
        """
        container_name, old_blob_name = self.extract_blob_info_from_url(
            old_blob_url)

        try:
            new_blob_name = f"{uuid.uuid4()}.{file_extension}"

            sas_token = generate_blob_sas(
                account_name=ACCOUNT_NAME,
                container_name=container_name,
                blob_name=new_blob_name,
                account_key=BLOB_SERVICE_CLIENT.credential.account_key,
                permission=BlobSasPermissions(write=True, create=True),
                expiry=datetime.now(timezone.utc) + timedelta(minutes=15),
                content_settings=ContentSettings(content_type=content_type)
            )

            upload_url = (
                f"https://{ACCOUNT_NAME}.blob.core.windows.net/"
                f"{container_name}/{new_blob_name}?{sas_token}"
            )

            delete_sas_token = generate_blob_sas(
                account_name=ACCOUNT_NAME,
                container_name=container_name,
                blob_name=old_blob_name,
                account_key=BLOB_SERVICE_CLIENT.credential.account_key,
                permission=BlobSasPermissions(delete=True),
                expiry=datetime.now(timezone.utc) + timedelta(minutes=15)
            )

            delete_url = (
                f"https://{ACCOUNT_NAME}.blob.core.windows.net/"
                f"{container_name}/{old_blob_name}?{delete_sas_token}"
            )

            return {
                "delete_url": delete_url,
                "new_blob_name": new_blob_name,
                "new_blob_url": upload_url
            }

        except Exception as e:
            raise AzureServiceError(
                "Failed to generate update SAS URL.") from e

    def generate_delete_sas_url(
        self,
        blob_url: str,
    ) -> dict:
        """
        Generates a SAS URL for deleting a blob from the specified container.
        """
        container_name, blob_name = self.extract_blob_info_from_url(blob_url)

        try:
            sas_token = generate_blob_sas(
                account_name=ACCOUNT_NAME,
                container_name=container_name,
                blob_name=blob_name,
                account_key=BLOB_SERVICE_CLIENT.credential.account_key,
                permission=BlobSasPermissions(delete=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=1)
            )

            delete_url = (
                f"https://{ACCOUNT_NAME}.blob.core.windows.net/"
                f"{container_name}/{blob_name}?{sas_token}"
            )

            return {
                "blob_url": delete_url
            }

        except Exception as e:
            raise AzureServiceError(
                "Failed to generate delete SAS URL.") from e

    def generate_read_sas_url(
        self,
        container_name: str,
        blob_name: str,
    ) -> str:
        """
        Generates a SAS URL for reading a blob from the specified container.
        """
        if container_name not in ALLOWED_CONTAINERS:
            raise InvalidContainerError("Invalid container name.")

        try:
            sas_token = generate_blob_sas(
                account_name=ACCOUNT_NAME,
                container_name=container_name,
                blob_name=blob_name,
                account_key=BLOB_SERVICE_CLIENT.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=1)
            )

            read_url = (
                f"https://{ACCOUNT_NAME}.blob.core.windows.net/"
                f"{container_name}/{blob_name}?{sas_token}"
            )

            return read_url

        except Exception as e:
            raise AzureServiceError("Failed to generate read SAS URL.") from e

    def extract_blob_info_from_url(self, blob_url: str) -> tuple[str, str]:
        """
        Extracts the container name and blob name from a given blob URL.
        """
        try:
            parsed_url = urlparse(blob_url)
            path_parts = parsed_url.path.strip('/').split('/', 1)

            if len(path_parts) < 2:
                raise ValueError("Invalid blob URL format")

            container_name = path_parts[0]
            blob_name = path_parts[1]

            return container_name, blob_name

        except Exception as e:
            raise AzureServiceError(
                "Failed to extract blob info from URL.") from e
