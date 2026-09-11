from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models import RetestComparison
from app.schemas.retest_comparison import RetestComparisonRead
from app.services import comparison_service

router = APIRouter(tags=["comparisons"])


@router.post("/comparisons", response_model=RetestComparisonRead, status_code=201)
def create_comparison(
    baseline_run_id: uuid.UUID, retest_run_id: uuid.UUID, session: Session = Depends(get_session)
):
    try:
        return comparison_service.compare(session, baseline_run_id, retest_run_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/applications/{application_id}/comparisons", response_model=list[RetestComparisonRead])
def list_comparisons(application_id: uuid.UUID, session: Session = Depends(get_session)):
    return list(
        session.exec(
            select(RetestComparison)
            .where(RetestComparison.application_id == application_id)
            .order_by(RetestComparison.created_at.desc())
        )
    )


@router.get("/comparisons/{comparison_id}", response_model=RetestComparisonRead)
def get_comparison(comparison_id: uuid.UUID, session: Session = Depends(get_session)):
    comparison = session.get(RetestComparison, comparison_id)
    if comparison is None:
        raise HTTPException(404, "Comparison not found")
    return comparison
