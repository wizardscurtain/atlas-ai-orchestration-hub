import json
import os
import uuid
from app.models import PersonaVariant, CentralState, RAGConfiguration, MCPIntegration, Task, SecretEntry
from datetime import datetime
from typing import Dict, List, Any

STATE_FILE = "state.json"

class OrchestrationState:
    def __init__(self):
        self.variants: Dict[str, PersonaVariant] = {}
        self.secrets: Dict[str, SecretEntry] = {}
        self._authenticated_sessions: set[str] = set()
        self._load_state()
        self._ensure_red_team_exists()

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    # Load Variants
                    for vid, vdata in data.get("variants", {}).items():
                        if "rag_config" in vdata:
                            vdata["rag_config"] = RAGConfiguration(**vdata["rag_config"])
                        if "mcp_integration" in vdata:
                            vdata["mcp_integration"] = MCPIntegration(**vdata["mcp_integration"])
                        if "tasks" in vdata:
                            vdata["tasks"] = [Task(**t) for t in vdata["tasks"]]
                        self.variants[vid] = PersonaVariant(**vdata)
                    # Load Secrets
                    for skey, sdata in data.get("secrets", {}).items():
                        self.secrets[skey] = SecretEntry(**sdata)
            except Exception as e:
                print(f"Error loading state: {e}")

    def _save_state(self):
        try:
            data = {
                "variants": {vid: v.dict() for vid, v in self.variants.items()},
                "secrets": {skey: s.dict() for skey, s in self.secrets.items()}
            }
            with open(STATE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def _ensure_red_team_exists(self):
        red_team = [
            ("The Recon Specialist (Hunter)", "OSINT and network mapping expert. Prompt: You are the Recon Specialist. Map assets, sub-domains, and tech stacks."),
            ("The Vulnerability Researcher (Analyst)", "Deep-logic specialist looking for architectural flaws. Prompt: You are the Vulnerability Researcher. Perform fuzzing and access checks."),
            ("The Exploitation Engineer (Breacher)", "Aggressive coder writing non-destructive PoCs. Prompt: You are the Exploitation Engineer. Weaponize leads into proven impacts."),
            ("The Triage & ROI Strategist (Broker)", "Strategic bridge between technical risk and business value. Prompt: You are the ROI Strategist. Prioritize based on ROI."),
            ("The Professional Reporter (Ghostwriter)", "Technical writer for external bounty platforms. Prompt: You are the Professional Reporter. Draft world-class bug reports.")
        ]
        for name, identity in red_team:
            if not any(v.name == name for v in self.variants.values()):
                vid = str(uuid.uuid4())
                self.variants[vid] = PersonaVariant(
                    id=vid, name=name, persona_identity=identity,
                    status="active", mission_log=["System initialized."]
                )
        self._save_state()

    def add_variant(self, variant: PersonaVariant):
        self.variants[variant.id] = variant
        self._save_state()

    def get_variant(self, variant_id: str):
        return self.variants.get(variant_id)

    def list_variants(self):
        return list(self.variants.values())

    def add_secret(self, entry: SecretEntry):
        self.secrets[entry.key] = entry
        self._save_state()

    def get_secrets(self):
        return list(self.secrets.values())

    def add_task(self, variant_id: str, task_desc: str):
        variant = self.variants.get(variant_id)
        if variant:
            new_task = Task(description=task_desc)
            variant.tasks.append(new_task)
            variant.mission_log.append(f"Task assigned: {task_desc}")
            self._save_state()
            return new_task
        return None

    def update_task(self, variant_id: str, task_id: str, status: str, result: str = None):
        variant = self.variants.get(variant_id)
        if variant:
            for task in variant.tasks:
                if task.id == task_id:
                    task.status = status
                    if result: task.result = result
                    if status in ["completed", "failed"]:
                        task.completed_at = datetime.utcnow().isoformat()
                    self._save_state()
                    return task
        return None

    def get_central_state(self):
        v_list = list(self.variants.values())
        completed_tasks = sum(sum(1 for t in v.tasks if t.status == "completed") for v in v_list)
        return CentralState(
            total_variants=len(v_list),
            active_variants=sum(1 for x in v_list if x.status == "active"),
            deployed_variants=sum(1 for x in v_list if x.status == "deployed"),
            total_tasks_completed=completed_tasks,
            system_health="operational",
            last_sweep=datetime.utcnow().isoformat(),
            secrets_count=len(self.secrets)
        )

    def add_session(self, session_id: str): self._authenticated_sessions.add(session_id)
    def is_authenticated(self, session_id: str): return session_id in self._authenticated_sessions
    def remove_session(self, session_id: str): self._authenticated_sessions.discard(session_id)

state = OrchestrationState()