import secrets
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Cookie, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import PersonaVariant, PersonaVariantCreate, PersonaVariantUpdate, SecretEntry
from app.state import state

APP_PASSWORD = "AtlasMaster2026"

app = FastAPI(title="Atlas AI Orchestration Hub", version="1.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def require_auth(session_id: str = Cookie(None)):
    if not session_id or not state.is_authenticated(session_id):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_id

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request, session_id: str = Cookie(None)):
    if session_id and state.is_authenticated(session_id):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/auth/login")
async def login(request: Request):
    form = await request.form()
    if form.get("password") == APP_PASSWORD:
        sid = secrets.token_hex(32)
        state.add_session(sid)
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_id", value=sid, httponly=True, samesite="lax")
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, sid: str = Depends(require_auth)):
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "state": state.get_central_state(), "variants": state.list_variants(),
    })

@app.get("/variants/{variant_id}", response_class=HTMLResponse)
async def variant_detail(request: Request, variant_id: str, sid: str = Depends(require_auth)):
    variant = state.get_variant(variant_id)
    if not variant: raise HTTPException(status_code=404)
    return templates.TemplateResponse("variant_detail.html", {"request": request, "variant": variant})

@app.get("/warchest", response_class=HTMLResponse)
async def warchest_page(request: Request, sid: str = Depends(require_auth)):
    return templates.TemplateResponse("warchest.html", {"request": request, "secrets": state.get_secrets()})

@app.post("/api/variants/{variant_id}/tasks")
async def assign_task(variant_id: str, description: str = Form(...), sid: str = Depends(require_auth)):
    state.add_task(variant_id, description)
    return RedirectResponse(url=f"/variants/{variant_id}", status_code=303)

@app.post("/api/warchest/add")
async def add_secret(key: str = Form(...), value: str = Form(...), description: str = Form(None), sid: str = Depends(require_auth)):
    state.add_secret(SecretEntry(key=key, value=value, description=description))
    return RedirectResponse(url="/warchest", status_code=303)

@app.get("/api/master/sync")
async def sync_state():
    return {
        "fleet": state.list_variants(),
        "warchest": state.get_secrets(),
        "central": state.get_central_state()
    }

@app.post("/api/master/task-update")
async def master_task_update(variant_id: str, task_id: str, status: str, result: str = None):
    state.update_task(variant_id, task_id, status, result)
    return {"status": "ok"}

@app.exception_handler(401)
async def auth_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/", status_code=303)