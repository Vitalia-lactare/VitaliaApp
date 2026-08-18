from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..config import ADMIN_PASSWORD, ADMIN_USERNAME
from ..templating import templates

router = APIRouter(prefix="/admin")


def require_admin(request: Request) -> None:
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


@router.get("/login")
def admin_login_form(request: Request):
    if request.session.get("is_admin"):
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    return templates.TemplateResponse(request, "admin_login.html", {"request": request, "erro": False})


@router.post("/login")
def admin_login_submit(request: Request, usuario: str = Form(...), senha: str = Form(...)):
    if usuario == ADMIN_USERNAME and senha == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    ctx = {"request": request, "erro": True}
    return templates.TemplateResponse(request, "admin_login.html", ctx, status_code=401)


@router.get("/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)
