from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceRead, status_code=201)
def create_workspace(data: WorkspaceCreate, session: Session = Depends(get_session)):
    workspace = Workspace(**data.model_dump())
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(session: Session = Depends(get_session)):
    return list(session.exec(select(Workspace)))


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(workspace_id: uuid.UUID, session: Session = Depends(get_session)):
    workspace = session.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace(
    workspace_id: uuid.UUID, data: WorkspaceUpdate, session: Session = Depends(get_session)
):
    workspace = session.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(workspace, key, value)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(workspace_id: uuid.UUID, session: Session = Depends(get_session)):
    workspace = session.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    session.delete(workspace)
    session.commit()
