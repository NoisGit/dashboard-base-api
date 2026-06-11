"""Upload validation shared by bulk-import services."""

from fastapi import HTTPException, UploadFile, status

CSV_UPLOAD_MAX_BYTES = 5 * 1024 * 1024
CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
    "application/octet-stream",
}


def validate_csv_upload(file: UploadFile, content: bytes) -> None:
    """Validate CSV metadata and size before parsing user-controlled content."""
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in CSV_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV content type.",
        )
    if len(content) > CSV_UPLOAD_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="CSV file cannot exceed 5 MB.",
        )
