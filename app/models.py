from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class MCPIntegration(BaseModel):
    web_search: bool = False
    file_analysis: bool = False
    email_integration: bool = False
    calendar_sync: bool = False
    code_execution: bool = False
    data_extraction: bool = False
    image_generation: bool = False
    memory_access: bool = False

class RAGConfiguration(BaseModel):
    endpoint_url: str = ""
    api_key: str = ""
    collection_name: str = ""
    enabled: bool = False

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    status: str = "pending" # pending, running, completed, failed
    result: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

class PersonaVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    persona_identity: str
    rag_config: RAGConfiguration = Field(default_factory=RAGConfiguration)
    mcp_integration: MCPIntegration = Field(default_factory=MCPIntegration)
    status: str = "inactive"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: Optional[str] = None
    mission_log: List[str] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)

class CentralState(BaseModel):
    total_variants: int = 0
    active_variants: int = 0
    deployed_variants: int = 0
    total_tasks_completed: int = 0
    system_health: str = "operational"
    last_sweep: Optional[str] = None
    secrets_count: int = 0

class SecretEntry(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())