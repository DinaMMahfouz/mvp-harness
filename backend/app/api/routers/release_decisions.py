from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.models import Application, ReleaseDecision, TestRun
from app.api.deps import get_session
from app.schemas.release_decision import ReleaseDecisionRead
from app.services import scoring_service

router = APIRouter(tags=["release-decisions"])


@router.post(
    "/runs/{run_id}/release-decision/recompute",
    response_model=ReleaseDecisionRead,
    status_code=201,
)
def recompute_release_decision(run_id: uuid.UUID, session: Session = Depends(get_session)):
    run = session.get(TestRun, run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    application = session.get(Application, run.application_id)
    if application is None:
        raise HTTPException(404, "Application not found")

    if run.assurance_score is None:
        scoring_service.score_run(session, run)
        session.refresh(run)

    result = scoring_service.decide_release(session, application, run)

    decision = ReleaseDecision(
        application_id=application.id,
        test_run_id=run.id,
        decision=result.decision,
        blocking_findings_count=result.blocking_findings_count,
        conditions=result.conditions,
        assurance_score=run.assurance_score or 0.0,
        rationale=result.rationale,
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)
    return decision


@router.get("/applications/{application_id}/release-decisions", response_model=list[ReleaseDecisionRead])
def list_release_decisions(application_id: uuid.UUID, session: Session = Depends(get_session)):
    return list(
        session.exec(
            select(ReleaseDecision)
            .where(ReleaseDecision.application_id == application_id)
            .order_by(ReleaseDecision.decided_at.desc())
        )
    )


@router.get("/runs/{run_id}/release-decision", response_model=ReleaseDecisionRead)
def get_latest_release_decision_for_run(run_id: uuid.UUID, session: Session = Depends(get_session)):
    decision = session.exec(
        select(ReleaseDecision)
        .where(ReleaseDecision.test_run_id == run_id)
        .order_by(ReleaseDecision.decided_at.desc())
    ).first()
    if decision is None:
        raise HTTPException(404, "No release decision found for this run")
    return decision
