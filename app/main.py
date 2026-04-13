import os
import secrets
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from dotenv import load_dotenv

from app.models import PersonaVariant, PersonaVariantCreate
from app.state import state

ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "static"
TEMPLATES_DIR = ROOT_DIR / "templates"

load_dotenv(ROOT_DIR / ".env")
STATIC_DIR.mkdir(exist_ok=True)
APP_PASSWORD = os.environ["APP_PASSWORD"]

app = FastAPI(title="Atlas AI Orchestration Hub", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def require_auth(session_id: Optional[str] = Cookie(None)):
    if not session_id or not state.is_authenticated(session_id):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_id


# --- Auth Routes ---

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request, session_id: Optional[str] = Cookie(None)):
    if session_id and state.is_authenticated(session_id):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/auth/login")
async def login(request: Request):
    form = await request.form()
    password = form.get("password", "")
    if password == APP_PASSWORD:
        sid = secrets.token_hex(32)
        state.add_session(sid)
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="session_id", value=sid, httponly=True, samesite="lax")
        return response
    return templates.TemplateResponse(request, "login.html", {"error": "Invalid password"})


@app.get("/auth/logout")
async def logout(session_id: Optional[str] = Cookie(None)):
    if session_id:
        state.remove_session(session_id)
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_id")
    return response


# --- Dashboard Pages ---

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, sid: str = Depends(require_auth)):
    central = state.get_central_state()
    variants = state.list_variants()
    return templates.TemplateResponse(request, "dashboard.html", {
        "state": central,
        "variants": variants,
    })


@app.get("/variants/new", response_class=HTMLResponse)
async def new_variant_page(request: Request, sid: str = Depends(require_auth)):
    return templates.TemplateResponse(request, "variant_form.html", {"variant": None, "edit": False})


@app.get("/variants/{variant_id}", response_class=HTMLResponse)
async def variant_detail(request: Request, variant_id: str, sid: str = Depends(require_auth)):
    variant = state.get_variant(variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return templates.TemplateResponse(request, "variant_detail.html", {"variant": variant})


@app.get("/variants/{variant_id}/edit", response_class=HTMLResponse)
async def edit_variant_page(request: Request, variant_id: str, sid: str = Depends(require_auth)):
    variant = state.get_variant(variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return templates.TemplateResponse(request, "variant_form.html", {"variant": variant, "edit": True})


# --- API Routes ---

@app.get("/api/state")
async def api_central_state(sid: str = Depends(require_auth)):
    return state.get_central_state()


@app.get("/api/variants")
async def api_list_variants(sid: str = Depends(require_auth)):
    return state.list_variants()


@app.post("/api/variants")
async def api_create_variant(request: Request, sid: str = Depends(require_auth)):
    form = await request.form()
    mcp_data = {
        "web_search": form.get("mcp_web_search") == "on",
        "file_analysis": form.get("mcp_file_analysis") == "on",
        "email_integration": form.get("mcp_email_integration") == "on",
        "calendar_sync": form.get("mcp_calendar_sync") == "on",
        "code_execution": form.get("mcp_code_execution") == "on",
        "data_extraction": form.get("mcp_data_extraction") == "on",
        "image_generation": form.get("mcp_image_generation") == "on",
        "memory_access": form.get("mcp_memory_access") == "on",
    }
    rag_data = {
        "endpoint_url": form.get("rag_endpoint_url", ""),
        "api_key": form.get("rag_api_key", ""),
        "collection_name": form.get("rag_collection_name", ""),
        "enabled": form.get("rag_enabled") == "on",
    }
    from app.models import MCPIntegration, RAGConfiguration
    create = PersonaVariantCreate(
        name=form.get("name", ""),
        persona_identity=form.get("persona_identity", ""),
        rag_config=RAGConfiguration(**rag_data),
        mcp_integration=MCPIntegration(**mcp_data),
    )
    variant = PersonaVariant(
        name=create.name,
        persona_identity=create.persona_identity,
        rag_config=create.rag_config,
        mcp_integration=create.mcp_integration,
    )
    state.add_variant(variant)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.post("/api/variants/{variant_id}")
async def api_update_variant(request: Request, variant_id: str, sid: str = Depends(require_auth)):
    variant = state.get_variant(variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    form = await request.form()
    from app.models import MCPIntegration, RAGConfiguration
    mcp_data = {
        "web_search": form.get("mcp_web_search") == "on",
        "file_analysis": form.get("mcp_file_analysis") == "on",
        "email_integration": form.get("mcp_email_integration") == "on",
        "calendar_sync": form.get("mcp_calendar_sync") == "on",
        "code_execution": form.get("mcp_code_execution") == "on",
        "data_extraction": form.get("mcp_data_extraction") == "on",
        "image_generation": form.get("mcp_image_generation") == "on",
        "memory_access": form.get("mcp_memory_access") == "on",
    }
    rag_data = {
        "endpoint_url": form.get("rag_endpoint_url", ""),
        "api_key": form.get("rag_api_key", ""),
        "collection_name": form.get("rag_collection_name", ""),
        "enabled": form.get("rag_enabled") == "on",
    }
    updates = {
        "name": form.get("name"),
        "persona_identity": form.get("persona_identity"),
        "rag_config": RAGConfiguration(**rag_data),
        "mcp_integration": MCPIntegration(**mcp_data),
    }
    state.update_variant(variant_id, updates)
    return RedirectResponse(url=f"/variants/{variant_id}", status_code=302)


@app.post("/api/variants/{variant_id}/activate")
async def api_activate(variant_id: str, sid: str = Depends(require_auth)):
    v = state.activate_variant(variant_id)
    if not v:
        raise HTTPException(status_code=404)
    return RedirectResponse(url=f"/variants/{variant_id}", status_code=302)


@app.post("/api/variants/{variant_id}/deploy")
async def api_deploy(variant_id: str, sid: str = Depends(require_auth)):
    v = state.deploy_variant(variant_id)
    if not v:
        raise HTTPException(status_code=404)
    return RedirectResponse(url=f"/variants/{variant_id}", status_code=302)


@app.post("/api/variants/{variant_id}/deactivate")
async def api_deactivate(variant_id: str, sid: str = Depends(require_auth)):
    v = state.deactivate_variant(variant_id)
    if not v:
        raise HTTPException(status_code=404)
    return RedirectResponse(url=f"/variants/{variant_id}", status_code=302)


@app.post("/api/variants/{variant_id}/delete")
async def api_delete(variant_id: str, sid: str = Depends(require_auth)):
    if not state.delete_variant(variant_id):
        raise HTTPException(status_code=404)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.exception_handler(401)
async def auth_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/", status_code=302)
