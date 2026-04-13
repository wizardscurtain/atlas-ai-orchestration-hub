# Atlas AI Orchestration Hub

A password-protected AI drone fleet command center for managing specialized persona variants. Each variant is configurable with its own identity, RAG pipeline, and MCP tool access — designed as a drone that communicates back to a central orchestration state.

## Architecture

```
┌───────────────────────────────────────┐
│         Central Command (Hub)       │
│  ┌───────────┐  ┌───────────────┐   │
│  │  FastAPI   │  │ Central State │   │
│  │  Server    │──│  Manager      │   │
│  └───────────┘  └───────────────┘   │
│        │                            │
│  ┌─────┴───────────────────────┐    │
│  │    Persona Variant Fleet    │    │
│  │  ┌──────┐ ┌──────┐ ┌─────┐ │    │
│  │  │Drone │ │Drone │ │Drone│ │    │
│  │  │Alpha │ │Bravo │ │  N  │ │    │
│  │  └──┬───┘ └──┬───┘ └──┬──┘ │    │
│  │     │        │        │     │    │
│  │  ┌──┴───┐ ┌──┴──┐ ┌──┴──┐  │    │
│  │  │ RAG  │ │ MCP │ │State│  │    │
│  │  │Config│ │Tools│ │ Log │  │    │
│  │  └──────┘ └─────┘ └─────┘  │    │
│  └─────────────────────────────┘    │
└───────────────────────────────────────┘
```

## Features

- **Password-Protected Access**: Landing page with authentication (password: `AtlasMaster2026`)
- **Central Dashboard**: Real-time overview of all drone variants — active count, deployed count, tool usage, RAG endpoints
- **Persona Variant CRUD**: Create, view, edit, and delete AI persona variants
- **RAG Configuration**: Per-variant vector DB endpoint, API key, and collection name
- **MCP Tool Toggles**: 8 tool integrations (web search, file analysis, email, calendar, code execution, data extraction, image generation, memory access)
- **Drone Lifecycle**: Activate → Deploy → Deactivate workflow with mission logging
- **Central State**: Aggregated fleet statistics and health monitoring

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Open http://localhost:8000
# Password: AtlasMaster2026
```

## Project Structure

```
ai-orchestration-hub/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI routes (auth, dashboard, API)
│   ├── models.py         # Pydantic models (PersonaVariant, MCP, RAG, CentralState)
│   └── state.py          # In-memory central state manager
├── templates/
│   ├── base.html          # Base layout with Tailwind
│   ├── login.html         # Password authentication page
│   ├── dashboard.html     # Main command center
│   ├── variant_form.html  # Create/edit persona variant
│   └── variant_detail.html # Variant detail + controls
├── static/
├── tests/
│   └── test_app.py
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Landing/login page |
| `POST` | `/auth/login` | Authenticate |
| `GET` | `/auth/logout` | Logout |
| `GET` | `/dashboard` | Main command center |
| `GET` | `/variants/new` | New variant form |
| `GET` | `/variants/{id}` | Variant detail page |
| `GET` | `/variants/{id}/edit` | Edit variant form |
| `GET` | `/api/state` | Central state JSON |
| `GET` | `/api/variants` | List all variants JSON |
| `POST` | `/api/variants` | Create variant |
| `POST` | `/api/variants/{id}` | Update variant |
| `POST` | `/api/variants/{id}/activate` | Activate drone |
| `POST` | `/api/variants/{id}/deploy` | Deploy drone |
| `POST` | `/api/variants/{id}/deactivate` | Deactivate drone |
| `POST` | `/api/variants/{id}/delete` | Delete variant |

## Future Extensions

- WebSocket for real-time drone-to-hub communication
- Persistent storage (SQLite/PostgreSQL)
- Drone task queuing and execution engine
- Inter-drone communication protocols
- Audit logging and replay
