"""Legacy storage service compatibility wrapper."""

from src.services.storage_service import StorageService


class AzureService(StorageService):
    """Backward-compatible alias for legacy service dependencies."""

    def generate_sas_upload_url(
        self,
        container_name: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Compatibility wrapper for old upload URL method name."""
        return self.generate_upload_url(
            container_name=container_name,
            file_extension=file_extension,
            content_type=content_type,
        )

    def generate_sas_update_url(
        self,
        old_blob_url: str,
        file_extension: str,
        content_type: str,
    ) -> dict:
        """Compatibility wrapper for old update URL method name."""
        return self.generate_update_url(
            old_blob_url=old_blob_url,
            file_extension=file_extension,
            content_type=content_type,
        )

    def generate_delete_sas_url(self, blob_url: str) -> dict:
        """Compatibility wrapper for old delete URL method name."""
        return self.generate_delete_url(blob_url=blob_url)

    def generate_read_sas_url(self, container_name: str, blob_name: str) -> str:
        """Compatibility wrapper for old read URL method name."""
        return self.generate_read_url(
            container_name=container_name,
            blob_name=blob_name,
        )
