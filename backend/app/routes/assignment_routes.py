import os
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from app.database import run_query
from app.auth import get_user_from_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "app/uploads"


@router.get("/assignments", response_class=HTMLResponse)
def assignments(request: Request):
    user = get_user_from_session(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    assignment_rows = run_query("SELECT * FROM assignments ORDER BY id", fetchall=True)
    submissions = run_query(
        "SELECT * FROM submissions WHERE user_id=%s ORDER BY submitted_at DESC",
        (user["id"],),
        fetchall=True,
    )
    return templates.TemplateResponse(
        "assignments.html",
        {"request": request, "user": user, "assignments": assignment_rows, "submissions": submissions},
    )


@router.post("/assignments/upload")
def upload_assignment(
    request: Request,
    assignment_id: int = Form(...),
    file: UploadFile = File(...),
):
    user = get_user_from_session(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{user['id']}_{assignment_id}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as out:
        out.write(file.file.read())

    run_query(
        """
        INSERT INTO submissions (assignment_id, user_id, filename, file_path, notes)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (assignment_id, user["id"], file.filename, filename, "Uploaded through portal"),
        commit=True,
    )

    return RedirectResponse("/assignments", status_code=302)


@router.get("/uploads/{filename}")
def get_upload(filename: str,request: Request):
    user = get_user_from_session(request)


    submission = run_query(
        """
        SELECT * FROM submissions WHERE user_id=%s AND file_path=%s
        """,
        (user["id"], filename),
        fetchone=True,
    )
    
    if not submission:
        return RedirectResponse("/assignments", status_code=404)
    

    path = os.path.join(UPLOAD_DIR, filename)
    return FileResponse(path)
    