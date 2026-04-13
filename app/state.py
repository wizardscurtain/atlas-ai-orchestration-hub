import json
import os
from app.models import PersonaVariant, CentralState, RAGConfiguration, MCPIntegration
from datetime import datetime

STATE_FILE = "state.json"

class OrchestrationState:
    """Persistent state manager for all persona variants (drone fleet)."""

    def __init__(self):
        self.variants: dict[str, PersonaVariant] = {}
        self._authenticated_sessions: set[str] = set()
        self._load_state()

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    for vid, vdata in data.get("variants", {}).items():
                        # Reconstruct nested models
                        if "rag_config" in vdata:
                            vdata["rag_config"] = RAGConfiguration(**vdata["rag_config"])
                        if "mcp_integration" in vdata:
                            vdata["mcp_integration"] = MCPIntegration(**vdata["mcp_integration"])
                        self.variants[vid] = PersonaVariant(**vdata)
            except Exception as e:
                print(f"Error loading state: {e}")

    def _save_state(self):
        try:
            data = {
                "variants": {vid: v.dict() for vid, v in self.variants.items()}
            }
            with open(STATE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def add_variant(self, variant: PersonaVariant) -> PersonaVariant:
        self.variants[variant.id] = variant
        self._save_state()
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
        self._save_state()
        return variant

    def delete_variant(self, variant_id: str) -> bool:
        if variant_id in self.variants:
            del self.variants[variant_id]
            self._save_state()
            return True
        return False

    def activate_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.variants.get(variant_id)
        if variant:
            variant.status = "active"
            variant.last_active = datetime.utcnow().isoformat()
            variant.mission_log.append(f"Activated at {variant.last_active}")
            self._save_state()
        return variant

    def deploy_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.variants.get(variant_id)
        if variant:
            variant.status = "deployed"
            variant.last_active = datetime.utcnow().isoformat()
            variant.mission_log.append(f"Deployed at {variant.last_active}")
            self._save_state()
        return variant

    def deactivate_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.variants.get(variant_id)
        if variant:
            variant.status = "inactive"
            variant.mission_log.append(f"Deactivated at {datetime.utcnow().isoformat()}")
            self._save_state()
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