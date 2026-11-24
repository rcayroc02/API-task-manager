from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import TaskNotFoundError
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, owner: User, data: TaskCreate) -> Task:
    task = Task(**data.model_dump(), owner_id=owner.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, owner: User, task_id: int) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == owner.id))
    if task is None:
        raise TaskNotFoundError
    return task


def list_tasks(
    db: Session,
    owner: User,
    *,
    status: TaskStatus | None,
    order_by: Literal["created_at", "due_date"],
    direction: Literal["asc", "desc"],
    limit: int,
    offset: int,
) -> tuple[list[Task], int]:
    query = select(Task).where(Task.owner_id == owner.id)
    if status is not None:
        query = query.where(Task.status == status)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    column = Task.due_date if order_by == "due_date" else Task.created_at
    ordering = column.asc() if direction == "asc" else column.desc()
    if order_by == "due_date":
        ordering = ordering.nulls_last()

    tasks = db.scalars(query.order_by(ordering, Task.id).limit(limit).offset(offset)).all()
    return list(tasks), total


def update_task(db: Session, owner: User, task_id: int, data: TaskUpdate) -> Task:
    task = get_task(db, owner, task_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, owner: User, task_id: int) -> None:
    task = get_task(db, owner, task_id)
    db.delete(task)
    db.commit()
