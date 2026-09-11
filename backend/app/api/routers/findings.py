from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_session
from app.models import Finding, FindingStatus, Remediation
from app.schemas.finding import FindingRead, RemediationCreate, RemediationRead
from app.services.remediation_service import InvalidTransitionError, set_status

router = APIRouter(tags=["findings"])


@router.get("/applications/{application_id}/findings", response_model=list[FindingRead])
def list_findings(
    application_id: uuid.UUID,
    status: FindingStatus | None = None,
    session: Session = Depends(get_session),
):
    stmt = select(Finding).where(Finding.application_id == application_id)
    if status is not None:
        stmt = stmt.where(Finding.status == status)
    return list(session.exec(stmt))


@router.get("/findings/{finding_id}", response_model=FindingRead)
def get_finding(finding_id: uuid.UUID, session: Session = Depends(get_session)):
    finding = session.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(404, "Finding not found")
    return finding


@router.get("/findings/{finding_id}/remediations", response_model=list[RemediationRead])
def list_remediations(finding_id: uuid.UUID, session: Session = Depends(get_session)):
    return list(
        session.exec(
            select(Remediation)
            .where(Remediation.finding_id == finding_id)
            .order_by(Remediation.changed_at.asc())
        )
    )


@router.patch("/findings/{finding_id}/remediation", response_model=FindingRead)
def update_finding_status(
    finding_id: uuid.UUID,
    data: RemediationCreate,
    session: Session = Depends(get_session),
    user: str = Depends(get_current_user),
):
    finding = session.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(404, "Finding not found")
    try:
        return set_status(session, finding, data.status, data.note, data.changed_by or user)
    except InvalidTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
