from app.models import PersonaVariant, CentralState
from datetime import datetime


class OrchestrationState:
    """Central state manager for all persona variants (drone fleet)."""

    def __init__(self):
        self.variants: dict[str, PersonaVariant] = {}
        self._authenticated_sessions: set[str] = set()

    def add_variant(self, variant: PersonaVariant) -> PersonaVariant:
        self.variants[variant.id] = variant
        return variant

    def get_variant(self, variant_id: str) -> PersonaVariant | None:
        return self.variants.get(variant_id)

    def list_variants(self) -> list[PersonaVariant]:
        return list(self.variants.values())

    def update_variant(self, variant_id: str, updates: dict) -> PersonaVariant | None:
        variant = self.variants.get(variant_id)
        if not variant:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(variant, key):
                setattr(variant, key, value)
        return variant

    def delete_variant(self, variant_id: str) -> bool:
        if variant_id in self.variants:
            del self.variants[variant_id]
            return True
        return False

    def activate_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.variants.get(variant_id)
        if variant:
            variant.status = "active"
            variant.last_active = datetime.utcnow().isoformat()
            variant.mission_log.append(f"Activated at {variant.last_active}")
        return variant

    def deploy_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.variants.get(variant_id)
        if variant:
            variant.status = "deployed"
            variant.last_active = datetime.utcnow().isoformat()
            variant.mission_log.append(f"Deployed at {variant.last_active}")
        return variant

    def deactivate_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.variants.get(variant_id)
        if variant:
            variant.status = "inactive"
            variant.mission_log.append(f"Deactivated at {datetime.utcnow().isoformat()}")
        return variant

    def get_central_state(self) -> CentralState:
        variants = list(self.variants.values())
        active = sum(1 for v in variants if v.status == "active")
        deployed = sum(1 for v in variants if v.status == "deployed")
        mcp_tools = 0
        rag_count = 0
        for v in variants:
            mcp = v.mcp_integration
            mcp_tools += sum([
                mcp.web_search, mcp.file_analysis, mcp.email_integration,
                mcp.calendar_sync, mcp.code_execution, mcp.data_extraction,
                mcp.image_generation, mcp.memory_access,
            ])
            if v.rag_config.enabled:
                rag_count += 1
        return CentralState(
            total_variants=len(variants),
            active_variants=active,
            deployed_variants=deployed,
            total_mcp_tools_enabled=mcp_tools,
            rag_endpoints_configured=rag_count,
            system_health="operational",
            last_sweep=datetime.utcnow().isoformat(),
        )

    def add_session(self, session_id: str):
        self._authenticated_sessions.add(session_id)

    def is_authenticated(self, session_id: str) -> bool:
        return session_id in self._authenticated_sessions

    def remove_session(self, session_id: str):
        self._authenticated_sessions.discard(session_id)


state = OrchestrationState()
