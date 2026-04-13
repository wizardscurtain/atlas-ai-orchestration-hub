from pydantic import BaseModel, Field
from typing import Optional
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


class PersonaVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    persona_identity: str
    rag_config: RAGConfiguration = Field(default_factory=RAGConfiguration)
    mcp_integration: MCPIntegration = Field(default_factory=MCPIntegration)
    status: str = "inactive"  # inactive, active, deployed
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: Optional[str] = None
    mission_log: list[str] = Field(default_factory=list)


class PersonaVariantCreate(BaseModel):
    name: str
    persona_identity: str
    rag_config: RAGConfiguration = Field(default_factory=RAGConfiguration)
    mcp_integration: MCPIntegration = Field(default_factory=MCPIntegration)


class PersonaVariantUpdate(BaseModel):
    name: Optional[str] = None
    persona_identity: Optional[str] = None
    rag_config: Optional[RAGConfiguration] = None
    mcp_integration: Optional[MCPIntegration] = None
    status: Optional[str] = None


class CentralState(BaseModel):
    total_variants: int = 0
    active_variants: int = 0
    deployed_variants: int = 0
    total_mcp_tools_enabled: int = 0
    rag_endpoints_configured: int = 0
    system_health: str = "operational"
    last_sweep: Optional[str] = None
