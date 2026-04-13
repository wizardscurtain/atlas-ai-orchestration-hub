import os
import time

from pymongo import ASCENDING, MongoClient

from app.models import CentralState, PersonaVariant, utc_now_iso


class VariantStoreProxy:
    def __init__(self, store: "OrchestrationState"):
        self.store = store

    def clear(self):
        self.store.get_variants_collection().delete_many({})

    def values(self):
        return self.store.list_variants()

    def keys(self):
        return [variant.id for variant in self.store.list_variants()]

    def __len__(self):
        return self.store.get_variants_collection().count_documents({})


class SessionStoreProxy:
    def __init__(self, store: "OrchestrationState"):
        self.store = store

    def clear(self):
        self.store.get_sessions_collection().delete_many({})


class OrchestrationState:
    """Central state manager for all persona variants (drone fleet)."""

    def __init__(self):
        self.mongo_url = os.environ["MONGO_URL"]
        self.db_name = os.environ["DB_NAME"]
        self.client = None
        self.db = None
        self.variants_collection = None
        self.sessions_collection = None
        self.variants = VariantStoreProxy(self)
        self._authenticated_sessions = SessionStoreProxy(self)

    def _connect(self) -> MongoClient:
        last_error = None
        for _ in range(30):
            try:
                client = MongoClient(self.mongo_url, serverSelectionTimeoutMS=5000)
                client.admin.command("ping")
                return client
            except Exception as exc:
                last_error = exc
                time.sleep(1)
        raise RuntimeError(f"Unable to connect to MongoDB: {last_error}")

    def _ensure_connection(self):
        if self.client is not None and self.db is not None and self.variants_collection is not None and self.sessions_collection is not None:
            return

        self.client = self._connect()
        self.db = self.client[self.db_name]
        self.variants_collection = self.db["variants"]
        self.sessions_collection = self.db["sessions"]
        self.variants_collection.create_index([("id", ASCENDING)], unique=True)
        self.sessions_collection.create_index([("session_id", ASCENDING)], unique=True)

    def get_variants_collection(self):
        self._ensure_connection()
        return self.variants_collection

    def get_sessions_collection(self):
        self._ensure_connection()
        return self.sessions_collection

    def _variant_from_doc(self, doc: dict | None) -> PersonaVariant | None:
        if not doc:
            return None
        doc.pop("_id", None)
        return PersonaVariant(**doc)

    def _save_variant(self, variant: PersonaVariant) -> PersonaVariant:
        payload = variant.model_dump()
        self.get_variants_collection().replace_one({"id": variant.id}, payload, upsert=True)
        return variant

    def add_variant(self, variant: PersonaVariant) -> PersonaVariant:
        return self._save_variant(variant)

    def get_variant(self, variant_id: str) -> PersonaVariant | None:
        doc = self.get_variants_collection().find_one({"id": variant_id}, {"_id": 0})
        return self._variant_from_doc(doc)

    def list_variants(self) -> list[PersonaVariant]:
        docs = self.get_variants_collection().find({}, {"_id": 0}).sort("created_at", ASCENDING)
        return [PersonaVariant(**doc) for doc in docs]

    def update_variant(self, variant_id: str, updates: dict) -> PersonaVariant | None:
        variant = self.get_variant(variant_id)
        if not variant:
            return None
        payload = variant.model_dump()
        for key, value in updates.items():
            if value is not None and key in payload:
                payload[key] = value.model_dump() if hasattr(value, "model_dump") else value
        return self._save_variant(PersonaVariant(**payload))

    def delete_variant(self, variant_id: str) -> bool:
        result = self.get_variants_collection().delete_one({"id": variant_id})
        return result.deleted_count == 1

    def activate_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.get_variant(variant_id)
        if variant:
            variant.status = "active"
            variant.last_active = utc_now_iso()
            variant.mission_log.append(f"Activated at {variant.last_active}")
            return self._save_variant(variant)
        return None

    def deploy_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.get_variant(variant_id)
        if variant:
            variant.status = "deployed"
            variant.last_active = utc_now_iso()
            variant.mission_log.append(f"Deployed at {variant.last_active}")
            return self._save_variant(variant)
        return None

    def deactivate_variant(self, variant_id: str) -> PersonaVariant | None:
        variant = self.get_variant(variant_id)
        if variant:
            variant.status = "inactive"
            variant.mission_log.append(f"Deactivated at {utc_now_iso()}")
            return self._save_variant(variant)
        return None

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
            last_sweep=utc_now_iso(),
        )

    def add_session(self, session_id: str):
        self.get_sessions_collection().replace_one(
            {"session_id": session_id},
            {"session_id": session_id, "created_at": utc_now_iso()},
            upsert=True,
        )

    def is_authenticated(self, session_id: str) -> bool:
        return self.get_sessions_collection().count_documents({"session_id": session_id}, limit=1) == 1

    def remove_session(self, session_id: str):
        self.get_sessions_collection().delete_one({"session_id": session_id})


state = OrchestrationState()
