"""Storage router module for Locentr uploads."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_storage_service
from src.schemas.storage_schemas import (
    StorageUploadRequest,
    StorageUpdateRequest,
    StorageDeleteRequest,
    StorageResponse,
    StorageUpdateResponse,
    StorageDeleteResponse,
    PrivateUploadResponse,
)
from src.services.storage_service import StorageService
from src.api.error import InvalidContainerError, StorageServiceError

router = APIRouter(prefix="/storage", tags=["storage"])

storage_roles = [
    UserRole.SUPERADMIN,
    UserRole.ADMIN,
    UserRole.CLIENT,
    UserRole.OPERATOR,
]


@router.put(
    "/private/upload/{token}",
    response_model=PrivateUploadResponse,
)
async def upload_private_document(
    token: str,
    request: Request,
    service: StorageService = Depends(get_storage_service),
) -> PrivateUploadResponse:
    """Store bytes authorized by a short-lived, tenant-bound upload token."""
    try:
        content = await request.body()
        object_name = service.store_private_upload(
            token=token,
            content=content,
            content_type=request.headers.get("content-type", ""),
        )
        return PrivateUploadResponse(object_name=object_name)
    except StorageServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/private/read/{token}", response_class=FileResponse)
async def read_private_document(
    token: str,
    service: StorageService = Depends(get_storage_service),
) -> FileResponse:
    """Read a private object using a short-lived signed URL."""
    try:
        path, file_name, content_type = service.resolve_private_read(token)
        return FileResponse(
            path=path,
            filename=file_name,
            media_type=content_type,
        )
    except StorageServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/generate_upload_url", response_model=StorageResponse)
async def generate_upload_url(
    request: StorageUploadRequest,
    service: StorageService = Depends(get_storage_service),
    _=Depends(RoleChecker(storage_roles)),
):
    """Generate an upload URL for a storage object."""
    try:
        result = service.generate_upload_url(
            container_name=request.container_name,
            file_extension=request.file_extension,
            content_type=request.content_type,
        )
        return StorageResponse(**result)
    except InvalidContainerError:
        raise
    except StorageServiceError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the upload URL.",
        ) from e


@router.post("/generate_update_url", response_model=StorageUpdateResponse)
async def generate_update_url(
    request: StorageUpdateRequest,
    service: StorageService = Depends(get_storage_service),
    _=Depends(RoleChecker(storage_roles)),
):
    """Generate replacement metadata for a storage object."""
    try:
        result = service.generate_update_url(
            old_object_url=request.old_object_url,
            file_extension=request.file_extension,
            content_type=request.content_type,
        )
        return StorageUpdateResponse(**result)
    except InvalidContainerError:
        raise
    except StorageServiceError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the update URL.",
        ) from e


@router.post("/generate_delete_url", response_model=StorageDeleteResponse)
async def generate_delete_url(
    request: StorageDeleteRequest,
    service: StorageService = Depends(get_storage_service),
    _=Depends(RoleChecker(storage_roles)),
):
    """Return delete metadata for a storage object."""
    try:
        result = service.generate_delete_url(object_url=request.object_url)
        return StorageDeleteResponse(**result)
    except InvalidContainerError:
        raise
    except StorageServiceError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the delete URL.",
        ) from e
