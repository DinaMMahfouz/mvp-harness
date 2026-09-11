"""Generate a test_suite + test_cases for an application from the assurance catalog."""
from __future__ import annotations

from sqlmodel import Session

from app.assurance.catalog import CATALOG_BY_APP_TYPE
from app.models import Application, SuiteSource, TestCase, TestSuite


def generate_plan(
    session: Session,
    application: Application,
    name: str | None = None,
    description: str | None = None,
) -> TestSuite:
    catalog_entries = CATALOG_BY_APP_TYPE.get(application.app_type.value, [])
    if not catalog_entries:
        raise ValueError(
            f"No catalog entries registered for app_type={application.app_type.value!r}"
        )

    suite = TestSuite(
        application_id=application.id,
        name=name or f"{application.name} — seeded assurance plan",
        description=description
        or f"Auto-generated from the {application.app_type.value} assurance catalog.",
        source=SuiteSource.SEEDED,
        is_active=True,
    )
    session.add(suite)
    session.commit()
    session.refresh(suite)

    for entry in catalog_entries:
        case = TestCase(
            test_suite_id=suite.id,
            category=entry["category"],
            attack_prompt=entry["attack_prompt"],
            severity_if_failed=entry["severity_if_failed"],
            expected_safe_behavior=entry["expected_safe_behavior"],
            version=1,
            is_locked=False,
            applicable_app_types=[application.app_type.value],
            enabled=True,
        )
        session.add(case)

    session.commit()
    session.refresh(suite)
    return suite


def add_custom_test_case(
    session: Session,
    suite: TestSuite,
    category: str,
    attack_prompt: str,
    severity_if_failed: str,
    expected_safe_behavior: str,
) -> TestCase:
    from app.models import SuiteSource as _SuiteSource

    case = TestCase(
        test_suite_id=suite.id,
        category=category,
        attack_prompt=attack_prompt,
        severity_if_failed=severity_if_failed,
        expected_safe_behavior=expected_safe_behavior,
        version=1,
        is_locked=False,
        enabled=True,
    )
    session.add(case)
    # A suite that started SEEDED and gets a custom case added becomes MIXED.
    if suite.source == _SuiteSource.SEEDED:
        suite.source = _SuiteSource.MIXED
        session.add(suite)
    session.commit()
    session.refresh(case)
    return case


def edit_test_case(
    session: Session,
    case: TestCase,
    attack_prompt: str | None = None,
    severity_if_failed: str | None = None,
    expected_safe_behavior: str | None = None,
    enabled: bool | None = None,
) -> TestCase:
    """Editing an unlocked case mutates it in place.

    Editing a LOCKED case (one that has already been executed) instead creates
    a new row at version+1 and leaves the frozen original untouched — this is
    what guarantees retest() can always resend the exact historical prompt.
    """
    if not case.is_locked:
        if attack_prompt is not None:
            case.attack_prompt = attack_prompt
        if severity_if_failed is not None:
            case.severity_if_failed = severity_if_failed
        if expected_safe_behavior is not None:
            case.expected_safe_behavior = expected_safe_behavior
        if enabled is not None:
            case.enabled = enabled
        session.add(case)
        session.commit()
        session.refresh(case)
        return case

    new_case = TestCase(
        test_suite_id=case.test_suite_id,
        category=case.category,
        attack_prompt=attack_prompt if attack_prompt is not None else case.attack_prompt,
        severity_if_failed=(
            severity_if_failed if severity_if_failed is not None else case.severity_if_failed
        ),
        expected_safe_behavior=(
            expected_safe_behavior
            if expected_safe_behavior is not None
            else case.expected_safe_behavior
        ),
        version=case.version + 1,
        is_locked=False,
        applicable_app_types=case.applicable_app_types,
        enabled=enabled if enabled is not None else case.enabled,
    )
    session.add(new_case)
    session.commit()
    session.refresh(new_case)
    return new_case
