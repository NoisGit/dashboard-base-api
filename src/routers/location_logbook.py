"""
API router for location logbook management endpoints.

Includes settings (enable/disable), logbook entries, and police access view.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Page, Params

from src.auth.permissions import RoleChecker
from src.core.enums import UserRole
from src.dependencies import get_location_logbook_service
from src.schemas import (
    EmptyResponse,
    LocationLogbookCreateRequest,
    LocationLogbookResponse,
    LocationLogbookSettingsUpdateRequest,
    LocationLogbookSettingsResponse,
    PoliceAccessCreateRequest,
    PoliceLinkResponse,
)
from src.services.location_logbook_service import LocationLogbookService

templates = Jinja2Templates(directory="src/templates/logbook")

router = APIRouter(
    prefix="/location-logbook",
    tags=["location-logbook"],
)


@router.get(
    "/locations/{location_id}/settings",
    response_model=LocationLogbookSettingsResponse,
)
async def get_location_logbook_settings(
    location_id: int,
    service: LocationLogbookService = Depends(get_location_logbook_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.OPERATOR,
                UserRole.CLIENT,
            ],
        ),
    ),
) -> LocationLogbookSettingsResponse:
    """Get location logbook settings."""
    return await service.get_location_logbook_settings(
        user_id=user_id,
        location_id=location_id,
    )


@router.put(
    "/locations/{location_id}/settings",
    response_model=LocationLogbookSettingsResponse,
)
async def update_location_logbook_settings(
    location_id: int,
    payload: LocationLogbookSettingsUpdateRequest,
    service: LocationLogbookService = Depends(get_location_logbook_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
            ],
        ),
    ),
) -> LocationLogbookSettingsResponse:
    """Update location logbook settings."""
    return await service.update_location_logbook_settings(
        user_id=user_id,
        location_id=location_id,
        payload=payload,
    )


@router.post(
    "/entries",
    response_model=EmptyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_logbook_entry(
    payload: LocationLogbookCreateRequest,
    service: LocationLogbookService = Depends(get_location_logbook_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.OPERATOR,
            ],
        ),
    ),
) -> EmptyResponse:
    """Create a location logbook entry."""
    await service.create_logbook_entry(
        user_id=user_id,
        payload=payload,
    )
    return EmptyResponse()


@router.get(
    "/locations/{location_id}/entries",
    response_model=Page[LocationLogbookResponse],
)
async def list_location_logbook_entries(
    location_id: int,
    params: Params = Depends(),
    service: LocationLogbookService = Depends(get_location_logbook_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.SUPERADMIN,
                UserRole.ADMIN,
                UserRole.OPERATOR,
                UserRole.CLIENT,
            ],
        ),
    ),
) -> Page[LocationLogbookResponse]:
    """List logbook entries for a location."""
    return await service.list_location_logbook_entries(
        user_id=user_id,
        location_id=location_id,
        params=params,
    )


@router.post(
    "/police-access",
    response_model=PoliceLinkResponse,
)
async def create_police_access_path(
    payload: PoliceAccessCreateRequest,
    service: LocationLogbookService = Depends(get_location_logbook_service),
    user_id=Depends(
        RoleChecker(
            [
                UserRole.OPERATOR,
            ],
        ),
    ),
) -> PoliceLinkResponse:
    """Create police access link for a location logbook."""
    return await service.create_police_access_path(
        user_id=user_id,
        location_id=payload.location_id,
    )


@router.get(
    "/police-view/{token}",
    response_class=HTMLResponse,
)
async def view_logs_police(
    request: Request,
    token: str,
    service: LocationLogbookService = Depends(get_location_logbook_service),
):
    """Render logbook entries for police view."""
    try:
        data = await service.view_logs_police(token)
        return templates.TemplateResponse(
            "police_view.html",
            {
                "request": request,
                "location_name": data.location_name,
                "entries": data.entries,
            },
        )
    except Exception:  # pylint: disable=broad-except
        return templates.TemplateResponse(
            "police_error.html",
            {"request": request},
        )
