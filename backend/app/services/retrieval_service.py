"""
services/retrieval_service.py — RAG retrieval across all 3 Qdrant collections.

Task: Week 7-8 / Embedding & Vector Database (task.md lines 391-396)
  [x] search_preferences(user_id, query) -> results
  [x] search_history(user_id, query, top_k=5) -> results
  [x] search_patterns(query, top_k=3) -> results
  [x] Combined search: run 3 queries in parallel
  [x] Result deduplication and ranking
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional

from qdrant_client.http import models as qdrant_models

from app.services.embedding_service import embedding_service
from app.services.qdrant_service import (
    qdrant_service,
    COLLECTION_USER_PREFERENCES,
    COLLECTION_CHAT_HISTORY,
    COLLECTION_PROMPT_PATTERNS,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """A single retrieved item from Qdrant with its score and source collection."""
    text: str              # The main text content
    score: float           # Similarity score (0.0 – 1.0, higher = more relevant)
    source: str            # Which collection this came from
    payload: dict          # Full payload for additional metadata


@dataclass
class CombinedContext:
    """
    The full RAG context to be injected into the augmented prompt.
    Each field is a list of retrieved items sorted by relevance.
    """
    preferences: List[RetrievalResult]
    history: List[RetrievalResult]
    patterns: List[RetrievalResult]


class RetrievalService:
    """
    Orchestrates RAG retrieval across all 3 Qdrant collections.

    The three collections serve different purposes:
      - user_preferences: Personalisation context (tone, domain, verbosity)
      - chat_history: Relevant past conversations from this user
      - prompt_patterns: High-quality prompt templates by domain
    """

    # ── Individual collection searches ───────────────────────────────────────

    def search_preferences(
        self, user_id: str, query: str
    ) -> List[RetrievalResult]:
        """
        Search the user's preference profile.
        Filtered to the current user only.
        """
        query_vector = embedding_service.embed_text(query)
        user_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="user_id",
                    match=qdrant_models.MatchValue(value=user_id),
                )
            ]
        )
        try:
            hits = qdrant_service.search(
                collection_name=COLLECTION_USER_PREFERENCES,
                query_vector=query_vector,
                filter_conditions=user_filter,
                top_k=1,  # One preference record per user is enough
            )
            return [
                RetrievalResult(
                    text=h.payload.get("preference_text", ""),
                    score=h.score,
                    source="preferences",
                    payload=h.payload,
                )
                for h in hits
                if h.payload.get("preference_text")
            ]
        except Exception as e:
            logger.warning(f"Preference search failed for user {user_id}: {e}")
            return []

    def search_history(
        self, user_id: str, query: str, top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Find the most semantically relevant past messages from this user.
        Filtered to the current user's chat history only.
        """
        query_vector = embedding_service.embed_text(query)
        user_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="user_id",
                    match=qdrant_models.MatchValue(value=user_id),
                )
            ]
        )
        try:
            hits = qdrant_service.search(
                collection_name=COLLECTION_CHAT_HISTORY,
                query_vector=query_vector,
                filter_conditions=user_filter,
                top_k=top_k,
            )
            return [
                RetrievalResult(
                    text=h.payload.get("content", ""),
                    score=h.score,
                    source="history",
                    payload=h.payload,
                )
                for h in hits
                if h.payload.get("content")
            ]
        except Exception as e:
            logger.warning(f"History search failed for user {user_id}: {e}")
            return []

    def search_patterns(
        self, query: str, top_k: int = 3, domain: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Find the most relevant prompt templates from the shared prompt_patterns library.
        Optionally filtered by domain (coding, writing, marketing, etc.).
        """
        query_vector = embedding_service.embed_text(query)

        domain_filter = None
        if domain and domain != "general":
            domain_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="domain",
                        match=qdrant_models.MatchValue(value=domain),
                    )
                ]
            )
        try:
            hits = qdrant_service.search(
                collection_name=COLLECTION_PROMPT_PATTERNS,
                query_vector=query_vector,
                filter_conditions=domain_filter,
                top_k=top_k,
            )
            return [
                RetrievalResult(
                    text=h.payload.get("template", ""),
                    score=h.score,
                    source="patterns",
                    payload=h.payload,
                )
                for h in hits
                if h.payload.get("template")
            ]
        except Exception as e:
            logger.warning(f"Pattern search failed: {e}")
            return []

    # ── Combined parallel search ──────────────────────────────────────────────

    def retrieve_context(
        self,
        user_id: str,
        query: str,
        domain: Optional[str] = None,
    ) -> CombinedContext:
        """
        Run all 3 searches and return the combined context.

        Executes all 3 searches sequentially here (sync context).
        For async parallel execution, use retrieve_context_async().
        """
        preferences = self.search_preferences(user_id, query)
        history = self.search_history(user_id, query, top_k=5)
        patterns = self.search_patterns(query, top_k=3, domain=domain)

        # Deduplicate results that appear in multiple collections
        seen_texts: set = set()
        deduped_history: List[RetrievalResult] = []
        for item in history:
            normalized = item.text.strip().lower()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                deduped_history.append(item)

        return CombinedContext(
            preferences=preferences,
            history=deduped_history,
            patterns=patterns,
        )

    async def retrieve_context_async(
        self,
        user_id: str,
        query: str,
        domain: Optional[str] = None,
    ) -> CombinedContext:
        """
        Async wrapper that runs all 3 searches in parallel via asyncio.
        Use this from FastAPI route handlers for best latency.
        """
        loop = asyncio.get_running_loop()

        # Run all 3 blocking calls in the thread pool concurrently
        prefs_task = loop.run_in_executor(
            None, self.search_preferences, user_id, query
        )
        history_task = loop.run_in_executor(
            None, self.search_history, user_id, query, 5
        )
        patterns_task = loop.run_in_executor(
            None, self.search_patterns, query, 3, domain
        )

        preferences, history, patterns = await asyncio.gather(
            prefs_task, history_task, patterns_task
        )

        # Deduplicate history results
        seen_texts: set = set()
        deduped_history: List[RetrievalResult] = []
        for item in history:
            normalized = item.text.strip().lower()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                deduped_history.append(item)

        return CombinedContext(
            preferences=preferences,
            history=deduped_history,
            patterns=patterns,
        )


# Module-level singleton
retrieval_service = RetrievalService()
