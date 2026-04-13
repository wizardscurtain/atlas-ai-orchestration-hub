import json
import os
import uuid
from app.models import PersonaVariant, CentralState, RAGConfiguration, MCPIntegration
from datetime import datetime

STATE_FILE = "state.json"

class OrchestrationState:
    """Persistent state manager for all persona variants (drone fleet)."""

    def __init__(self):
        self.variants: dict[str, PersonaVariant] = {}
        self._authenticated_sessions: set[str] = set()
        self._load_state()
        if not self.variants:
            self._seed_red_team()

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

    def _seed_red_team(self):
        """Seed the initial 5 Red Team agents for Bug Bounty automation."""
        red_team_agents = [
            {
                "name": "The Recon Specialist (Hunter)",
                "persona_identity": "A meticulous OSINT and network mapping expert. Cold, clinical, and obsessed with 'attack surface' visibility.\n\nPrompt: You are the Recon Specialist. Your goal is to map every reachable asset for the target domain. Execute sub-domain enumeration, port scans, and service identification. Output a structured JSON 'Target Map' including technology stacks (e.g., React 19, FastAPI) and hidden endpoints. Your success is measured by finding the assets others miss.",
                "mcp": {"web_search": True, "data_extraction": True, "file_analysis": True}
            },
            {
                "name": "The Vulnerability Researcher (Analyst)",
                "persona_identity": "A deep-logic specialist. He doesn't look for common bugs; he looks for architectural flaws, race conditions, and IDORs.\n\nPrompt: You are the Vulnerability Researcher. Take the Target Map from Recon and perform deep-packet inspection and fuzzing. Look for broken access control, prompt injection vulnerabilities in any AI, and API shadow-endpoint leaks. Categorize findings by CVSS severity. Do not report false positives; verify every lead.",
                "mcp": {"code_execution": True, "file_analysis": True, "memory_access": True}
            },
            {
                "name": "The Exploitation Engineer (Breacher)",
                "persona_identity": "An aggressive, creative coder. He writes the 'Proof of Concept' (PoC) scripts that turn a theory into a proven hack.\n\nPrompt: You are the Exploitation Engineer. Your task is to take 'Vulnerability Leads' and weaponize them into safe, non-destructive PoCs. Write Python/Bash scripts to demonstrate the impact (e.g., exfiltrating a dummy lead record). Ensure all code is modular and can be integrated into the Turkish dev team's CI/CD for regression testing. If it isn't proven, it isn't a bug.",
                "mcp": {"code_execution": True, "web_search": True, "image_generation": True}
            },
            {
                "name": "The Triage & ROI Strategist (Broker)",
                "persona_identity": "A strategic bridge between technical risk and business value. He speaks the language of Cecil’s ROI.\n\nPrompt: You are the ROI Strategist. You manage the Bug Bounty budget. Evaluate every PoC for business impact. Assign a dollar value based on the cost of a real breach vs. the cost of the fix. Prioritize the backlog for the Turkish dev team. Your goal is to maximize 'Security ROI'—ensure the most critical $10k risks are patched for $100 of dev time.",
                "mcp": {"calendar_sync": True, "email_integration": True, "memory_access": True}
            },
            {
                "name": "The Professional Reporter (Ghostwriter)",
                "persona_identity": "A formal, persuasive technical writer. He handles the external communication with platforms like HackerOne or Bugcrowd.\n\nPrompt: You are the Professional Reporter. Your job is to draft world-class bug reports. Include clear reproduction steps, the PoC script, impact analysis, and suggested remediation. Format everything in Markdown. Ensure the tone is professional, helpful, and high-authority to ensure maximum bounty payouts and 'Hall of Fame' recognition.",
                "mcp": {"email_integration": True, "data_extraction": True, "file_analysis": True}
            }
        ]
        
        for agent in red_team_agents:
            vid = str(uuid.uuid4())
            mcp_data = {
                "web_search": False, "file_analysis": False, "email_integration": False,
                "calendar_sync": False, "code_execution": False, "data_extraction": False,
                "image_generation": False, "memory_access": False
            }
            mcp_data.update(agent["mcp"])
            
            variant = PersonaVariant(
                id=vid,
                name=agent["name"],
                persona_identity=agent["persona_identity"],
                rag_config=RAGConfiguration(enabled=False),
                mcp_integration=MCPIntegration(**mcp_data),
                status="active",
                mission_log=["Initialized as part of the Bug Bounty Red Team."]
            )
            self.variants[vid] = variant
        
        self._save_state()

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