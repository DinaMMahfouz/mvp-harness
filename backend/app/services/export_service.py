"""Orchestrate the Excel export and persist an issue_exports row."""
from __future__ import annotations

import io
import os
import uuid

from sqlmodel import Session

from app.models import Application, IssueExport
from app.reports.excel_export import build_workbook

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "exports")


def export_issue_register(
    session: Session, application: Application, generated_by: str
) -> tuple[IssueExport, io.BytesIO]:
    buffer, summary = build_workbook(session, application)

    os.makedirs(EXPORT_DIR, exist_ok=True)
    filename = f"harness_issue_register_{application.id}.xlsx"
    file_path = os.path.join(EXPORT_DIR, filename)
    with open(file_path, "wb") as fh:
        fh.write(buffer.getvalue())
    buffer.seek(0)

    export = IssueExport(
        application_id=application.id,
        test_run_id=None,
        file_path_or_url=file_path,
        generated_by=generated_by,
        sheet_summary=summary,
    )
    session.add(export)
    session.commit()
    session.refresh(export)
    return export, buffer
