"""
services/qdrant_service.py — Qdrant vector database client and collection setup.

Task: Week 7-8 / Embedding & Vector Database (task.md lines 382-396)
  [x] Set up Qdrant collections:
      [x] user_preferences collection (384 dims, cosine distance)
      [x] chat_history collection (384 dims, cosine distance)
      [x] prompt_patterns collection (384 dims, cosine distance)
      [x] Configure payload indexes for filtering
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Collection names (single source of truth) ────────────────────────────────
COLLECTION_USER_PREFERENCES = "user_preferences"
COLLECTION_CHAT_HISTORY = "chat_history"
COLLECTION_PROMPT_PATTERNS = "prompt_patterns"

# all-MiniLM-L6-v2 produces 384-dimensional vectors
VECTOR_SIZE = 384
DISTANCE = qdrant_models.Distance.COSINE


class QdrantService:
    """
    Manages the Qdrant client and all collection lifecycle operations.

    Responsibilities:
    - Ensuring the 3 required collections exist on startup.
    - Upserting vectors with payload metadata.
    - Deleting vectors by point ID or user filter.
    """

    def __init__(self):
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        """Lazily create and cache the Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=10,
            )
        return self._client

    # ── Collection Bootstrap ────────────────────────────────────────────────

    def ensure_collections_exist(self) -> None:
        """
        Idempotently create all required Qdrant collections if they don't
        already exist. Called once at application startup.
        """
        for collection_name in [
            COLLECTION_USER_PREFERENCES,
            COLLECTION_CHAT_HISTORY,
            COLLECTION_PROMPT_PATTERNS,
        ]:
            # Use the official exists() check to avoid swallowing connection errors
            exists = self.client.collection_exists(collection_name)
            if not exists:
                logger.info(f"Creating Qdrant collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=DISTANCE,
                    ),
                )
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {collection_name}")

        # Create payload indexes for fast filtering
        self._create_payload_indexes()

    def _create_payload_indexes(self) -> None:
        """
        Create keyword indexes on common filter fields.
        These enable fast WHERE-like filtering inside Qdrant queries.
        """
        index_specs = [
            # user_preferences: filter by user_id
            (COLLECTION_USER_PREFERENCES, "user_id", qdrant_models.PayloadSchemaType.KEYWORD),
            # chat_history: filter by user_id and session_id
            (COLLECTION_CHAT_HISTORY, "user_id", qdrant_models.PayloadSchemaType.KEYWORD),
            (COLLECTION_CHAT_HISTORY, "session_id", qdrant_models.PayloadSchemaType.KEYWORD),
            # prompt_patterns: filter by domain
            (COLLECTION_PROMPT_PATTERNS, "domain", qdrant_models.PayloadSchemaType.KEYWORD),
        ]
        for collection, field, schema_type in index_specs:
            try:
                self.client.create_payload_index(
                    collection_name=collection,
                    field_name=field,
                    field_schema=schema_type,
                )
            except Exception:
                # Index may already exist; that's fine — Qdrant is idempotent here
                pass

    # ── Upsert Helpers ──────────────────────────────────────────────────────

    def upsert_preference(
        self,
        user_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """
        Upsert a user's preference embedding.
        One record per user — use the user UUID string as the deterministic point ID.
        """
        point_id = str(uuid.UUID(user_id))  # normalise to standard UUID format
        self.client.upsert(
            collection_name=COLLECTION_USER_PREFERENCES,
            points=[
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"user_id": user_id, **payload},
                )
            ],
        )

    def upsert_message(
        self,
        message_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """Upsert a chat message embedding into chat_history collection."""
        self.client.upsert(
            collection_name=COLLECTION_CHAT_HISTORY,
            points=[
                qdrant_models.PointStruct(
                    id=message_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def upsert_prompt_pattern(
        self,
        pattern_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """Upsert a prompt template/pattern into the prompt_patterns collection."""
        self.client.upsert(
            collection_name=COLLECTION_PROMPT_PATTERNS,
            points=[
                qdrant_models.PointStruct(
                    id=pattern_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    # ── Search Helpers ──────────────────────────────────────────────────────

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        filter_conditions: Optional[qdrant_models.Filter] = None,
        top_k: int = 5,
    ) -> List[Any]:
        """
        Perform a nearest-neighbour similarity search.

        Args:
            collection_name: Which collection to search.
            query_vector: The embedding of the query text.
            filter_conditions: Optional payload filter (e.g. filter by user_id).
            top_k: How many results to return.

        Returns:
            List of ScoredPoint objects sorted by score (highest first).
        """
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=filter_conditions,
            limit=top_k,
            with_payload=True,
        )

    def delete_by_user(self, collection_name: str, user_id: str) -> None:
        """Delete all points belonging to a specific user from a collection."""
        self.client.delete(
            collection_name=collection_name,
            points_selector=qdrant_models.FilterSelector(
                filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="user_id",
                            match=qdrant_models.MatchValue(value=user_id),
                        )
                    ]
                )
            ),
        )


# Module-level singleton
qdrant_service = QdrantService()
