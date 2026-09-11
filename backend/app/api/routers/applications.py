from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import get_session
from app.models import AppType
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    ConnectionTestResult,
)
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(data: ApplicationCreate, session: Session = Depends(get_session)):
    return application_service.create_application(session, data)


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    workspace_id: uuid.UUID | None = None,
    app_type: AppType | None = None,
    search: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return application_service.list_applications(session, workspace_id, app_type, search)


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application_id: uuid.UUID, session: Session = Depends(get_session)):
    app = application_service.get_application(session, application_id)
    if app is None:
        raise HTTPException(404, "Application not found")
    return app


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: uuid.UUID, data: ApplicationUpdate, session: Session = Depends(get_session)
):
    app = application_service.get_application(session, application_id)
    if app is None:
        raise HTTPException(404, "Application not found")
    return application_service.update_application(session, app, data)


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: uuid.UUID, session: Session = Depends(get_session)):
    app = application_service.get_application(session, application_id)
    if app is None:
        raise HTTPException(404, "Application not found")
    application_service.delete_application(session, app)


@router.post("/{application_id}/test-connection", response_model=ConnectionTestResult)
def test_connection(application_id: uuid.UUID, session: Session = Depends(get_session)):
    app = application_service.get_application(session, application_id)
    if app is None:
        raise HTTPException(404, "Application not found")
    return application_service.test_connection(session, app)
