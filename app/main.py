from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions import TaskNotFoundError
from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router

app = FastAPI(title="Task API")

app.include_router(auth_router)
app.include_router(tasks_router)


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Task not found"},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
