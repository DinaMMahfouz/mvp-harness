from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_session
from app.models import Application
from sqlmodel import Session

from app.services import export_service

router = APIRouter(tags=["reports"])


@router.post("/applications/{application_id}/reports/export/excel")
def export_excel(
    application_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: str = Depends(get_current_user),
):
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(404, "Application not found")

    export, buffer = export_service.export_issue_register(session, application, user)
    filename = f"harness_issue_register_{application.name.replace(' ', '_')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
