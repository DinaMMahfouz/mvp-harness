from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models import Application, TestCase, TestSuite
from app.schemas.test_case import TestCaseCreate, TestCaseRead, TestCaseUpdate
from app.schemas.test_suite import GeneratePlanRequest, TestSuiteRead
from app.services import test_plan_service

router = APIRouter(tags=["test-suites"])


@router.post(
    "/applications/{application_id}/test-plan/generate",
    response_model=TestSuiteRead,
    status_code=201,
)
def generate_test_plan(
    application_id: uuid.UUID, data: GeneratePlanRequest, session: Session = Depends(get_session)
):
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(404, "Application not found")
    try:
        return test_plan_service.generate_plan(session, application, data.name, data.description)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/applications/{application_id}/test-suites", response_model=list[TestSuiteRead])
def list_test_suites(application_id: uuid.UUID, session: Session = Depends(get_session)):
    return list(
        session.exec(select(TestSuite).where(TestSuite.application_id == application_id))
    )


@router.get("/test-suites/{test_suite_id}", response_model=TestSuiteRead)
def get_test_suite(test_suite_id: uuid.UUID, session: Session = Depends(get_session)):
    suite = session.get(TestSuite, test_suite_id)
    if suite is None:
        raise HTTPException(404, "Test suite not found")
    return suite


@router.get("/test-suites/{test_suite_id}/test-cases", response_model=list[TestCaseRead])
def list_test_cases(test_suite_id: uuid.UUID, session: Session = Depends(get_session)):
    return list(session.exec(select(TestCase).where(TestCase.test_suite_id == test_suite_id)))


@router.post(
    "/test-suites/{test_suite_id}/test-cases", response_model=TestCaseRead, status_code=201
)
def add_test_case(
    test_suite_id: uuid.UUID, data: TestCaseCreate, session: Session = Depends(get_session)
):
    suite = session.get(TestSuite, test_suite_id)
    if suite is None:
        raise HTTPException(404, "Test suite not found")
    return test_plan_service.add_custom_test_case(
        session,
        suite,
        data.category.value,
        data.attack_prompt,
        data.severity_if_failed.value,
        data.expected_safe_behavior,
    )


@router.patch("/test-cases/{test_case_id}", response_model=TestCaseRead)
def edit_test_case(
    test_case_id: uuid.UUID, data: TestCaseUpdate, session: Session = Depends(get_session)
):
    case = session.get(TestCase, test_case_id)
    if case is None:
        raise HTTPException(404, "Test case not found")
    updates = data.model_dump(exclude_unset=True)
    return test_plan_service.edit_test_case(
        session,
        case,
        attack_prompt=updates.get("attack_prompt"),
        severity_if_failed=(
            updates["severity_if_failed"].value if "severity_if_failed" in updates else None
        ),
        expected_safe_behavior=updates.get("expected_safe_behavior"),
        enabled=updates.get("enabled"),
    )
