from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_session
from app.models import Application, TestResult, TestRun, TestSuite
from app.schemas.test_result import TestResultRead
from app.schemas.test_run import ExecuteRunRequest, RetestRequest, TestRunRead
from app.services import retest_service, run_service

router = APIRouter(tags=["runs"])


@router.post("/applications/{application_id}/runs", response_model=TestRunRead, status_code=201)
def execute_run(
    application_id: uuid.UUID,
    data: ExecuteRunRequest,
    session: Session = Depends(get_session),
    user: str = Depends(get_current_user),
):
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(404, "Application not found")
    suite = session.get(TestSuite, data.test_suite_id)
    if suite is None or suite.application_id != application_id:
        raise HTTPException(404, "Test suite not found for this application")
    return run_service.execute_run(session, application, suite, data.triggered_by or user)


@router.get("/applications/{application_id}/runs", response_model=list[TestRunRead])
def list_runs(application_id: uuid.UUID, session: Session = Depends(get_session)):
    return list(
        session.exec(
            select(TestRun)
            .where(TestRun.application_id == application_id)
            .order_by(TestRun.created_at.desc())
        )
    )


@router.get("/runs/{run_id}", response_model=TestRunRead)
def get_run(run_id: uuid.UUID, session: Session = Depends(get_session)):
    run = session.get(TestRun, run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/runs/{run_id}/results", response_model=list[TestResultRead])
def get_run_results(run_id: uuid.UUID, session: Session = Depends(get_session)):
    return list(session.exec(select(TestResult).where(TestResult.test_run_id == run_id)))


@router.post(
    "/applications/{application_id}/retest", response_model=TestRunRead, status_code=201
)
def retest(
    application_id: uuid.UUID,
    data: RetestRequest,
    session: Session = Depends(get_session),
    user: str = Depends(get_current_user),
):
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(404, "Application not found")
    try:
        return retest_service.retest(
            session, application, data.based_on_run_id, data.scope, data.triggered_by or user
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
