"""Storage router module for Coredeck uploads."""

from fastapi import APIRouter, Depends, HTTPException, status

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
