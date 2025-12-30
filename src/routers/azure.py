"""
Azure router module for handling Azure Blob Storage operations.

This module provides FastAPI endpoints for generating SAS upload URLs
for Azure Blob Storage containers, including validation and error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.utils import get_current_user
from src.dependencies import get_azure_service
from src.schemas.azure_schemas import (
    AzureUploadRequest,
    AzureUpdateRequest,
    AzureDeleteRequest,
    AzureResponse,
    AzureUpdateResponse,
    AzureDeleteResponse,
)
from src.services.azure_service import AzureService
from src.api.error import (
    InvalidContainerError,
    AzureServiceError
)


router = APIRouter(prefix="/azure", tags=["Azure"])


@router.post("/generate_upload_url", response_model=AzureResponse)
async def generate_upload_url(
    request: AzureUploadRequest,
    service: AzureService = Depends(get_azure_service),
    _=Depends(get_current_user)
):
    """
    Generates a SAS upload URL for a specified Azure Blob Storage container and file type.
    """

    try:
        result = service.generate_sas_upload_url(
            container_name=request.container_name,
            file_extension=request.file_extension,
            content_type=request.content_type
        )

        return AzureResponse(**result)

    except InvalidContainerError:
        raise
    except AzureServiceError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the upload URL."
        ) from e


@router.post("/generate_update_url", response_model=AzureUpdateResponse)
async def generate_update_url(
    request: AzureUpdateRequest,
    service: AzureService = Depends(get_azure_service),
    _=Depends(get_current_user)
):
    """
    Generates a SAS update URL for a specified blob in an Azure Blob Storage container.
    """

    try:
        result = service.generate_sas_update_url(
            old_blob_url=request.old_blob_url,
            file_extension=request.file_extension,
            content_type=request.content_type
        )

        return AzureUpdateResponse(**result)

    except InvalidContainerError:
        raise
    except AzureServiceError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the update URL."
        ) from e


@router.post("/generate_delete_url", response_model=AzureDeleteResponse)
async def generate_delete_url(
    request: AzureDeleteRequest,
    service: AzureService = Depends(get_azure_service),
    _=Depends(get_current_user)
):
    """
    Generates a SAS delete URL for a specified blob in an Azure Blob Storage container.
    """

    try:
        result = service.generate_delete_sas_url(
            blob_url=request.blob_url
        )

        return AzureDeleteResponse(**result)

    except InvalidContainerError:
        raise
    except AzureServiceError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the delete URL."
        ) from e
