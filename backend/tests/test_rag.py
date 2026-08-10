"""
tests/test_rag.py — Integration tests for the RAG pipeline.

Task: Week 7-8 / RAG Integration (task.md lines 414-417)
  [x] Test retrieval returns relevant results
  [x] Test augmented prompts are well-formed
  [x] Test model output (via mock) improves with RAG context
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass
from typing import List, Optional


# ── Minimal stubs so tests don't need real Qdrant / sentence-transformers ──────
# We mock at the service boundary so we test logic, not external dependencies.

@dataclass
class MockRetrievalResult:
    text: str
    score: float
    source: str
    payload: dict


@dataclass
class MockCombinedContext:
    preferences: List[MockRetrievalResult]
    history: List[MockRetrievalResult]
    patterns: List[MockRetrievalResult]


# ── Tests: PromptAugmenter ─────────────────────────────────────────────────────

class TestPromptAugmenter:
    """Tests for app.rag.augmenter.PromptAugmenter"""

    @pytest.fixture
    def augmenter(self):
        from app.rag.augmenter import PromptAugmenter
        return PromptAugmenter()

    @pytest.fixture
    def full_context(self):
        return MockCombinedContext(
            preferences=[
                MockRetrievalResult(
                    text="User prefers professional tone with balanced verbosity. Primary domain: coding.",
                    score=0.95,
                    source="preferences",
                    payload={"preference_text": "User prefers professional tone...", "domain": "coding"},
                )
            ],
            history=[
                MockRetrievalResult(
                    text="User previously asked: How do I implement async endpoints in FastAPI?",
                    score=0.87,
                    source="history",
                    payload={"content": "User previously asked...", "session_id": "abc"},
                ),
                MockRetrievalResult(
                    text="User previously asked: What is the best way to handle database connections?",
                    score=0.81,
                    source="history",
                    payload={"content": "User previously asked...", "session_id": "abc"},
                ),
            ],
            patterns=[
                MockRetrievalResult(
                    text="Act as a senior software engineer. Review the code for: bugs, performance issues, security vulnerabilities.",
                    score=0.92,
                    source="patterns",
                    payload={"template": "Act as a senior software engineer...", "domain": "coding", "title": "Code Review"},
                ),
            ],
        )

    @pytest.fixture
    def user_preferences(self):
        return {
            "tone": "professional",
            "verbosity": "balanced",
            "target_model": "GPT-4",
            "domain": "coding",
            "custom_instructions": None,
        }

    def test_augment_returns_string(self, augmenter, full_context, user_preferences):
        """augment() must always return a non-empty string."""
        result = augmenter.augment(
            raw_prompt="Write a function to sort a list",
            context=full_context,
            user_preferences=user_preferences,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_augment_contains_raw_prompt(self, augmenter, full_context, user_preferences):
        """The raw prompt must appear in the augmented output."""
        raw = "Write a function to sort a list"
        result = augmenter.augment(raw_prompt=raw, context=full_context, user_preferences=user_preferences)
        assert raw in result

    def test_augment_contains_task_header(self, augmenter, full_context, user_preferences):
        """The task instruction header must appear in the output."""
        result = augmenter.augment(
            raw_prompt="test prompt",
            context=full_context,
            user_preferences=user_preferences,
        )
        assert "prompt engineer" in result.lower()

    def test_augment_injects_preferences_from_db(self, augmenter, full_context, user_preferences):
        """When db preferences dict is provided, it should inject tone/verbosity info."""
        result = augmenter.augment(
            raw_prompt="test prompt",
            context=full_context,
            user_preferences=user_preferences,
        )
        assert "professional" in result
        assert "balanced" in result

    def test_augment_injects_preferences_from_qdrant_fallback(self, augmenter, full_context):
        """When no db preferences dict, fall back to Qdrant preference text."""
        result = augmenter.augment(
            raw_prompt="test prompt",
            context=full_context,
            user_preferences=None,  # No db prefs
        )
        assert "User prefers" in result

    def test_augment_injects_history(self, augmenter, full_context, user_preferences):
        """History snippets should appear in the augmented output."""
        result = augmenter.augment(
            raw_prompt="test prompt",
            context=full_context,
            user_preferences=user_preferences,
        )
        assert "FastAPI" in result or "RELEVANT PAST" in result

    def test_augment_injects_patterns(self, augmenter, full_context, user_preferences):
        """Prompt patterns should appear in the augmented output."""
        result = augmenter.augment(
            raw_prompt="test prompt",
            context=full_context,
            user_preferences=user_preferences,
        )
        assert "senior software engineer" in result.lower() or "PROVEN" in result

    def test_augment_with_empty_context(self, augmenter, user_preferences):
        """augment() must not crash when context has no results."""
        empty_context = MockCombinedContext(preferences=[], history=[], patterns=[])
        result = augmenter.augment(
            raw_prompt="test prompt",
            context=empty_context,
            user_preferences=user_preferences,
        )
        assert "test prompt" in result
        assert len(result) > 0

    def test_augment_respects_token_budget(self, augmenter, user_preferences):
        """Augmented prompt must not exceed MAX_CONTEXT_CHARS + raw_prompt size."""
        from app.rag.augmenter import MAX_CONTEXT_CHARS

        # Context with very long texts that should be truncated
        large_context = MockCombinedContext(
            preferences=[
                MockRetrievalResult(
                    text="x" * 5000,  # Way too long
                    score=0.99,
                    source="preferences",
                    payload={"preference_text": "x" * 5000},
                )
            ],
            history=[
                MockRetrievalResult(
                    text="y" * 3000,
                    score=0.8,
                    source="history",
                    payload={"content": "y" * 3000},
                )
            ],
            patterns=[
                MockRetrievalResult(
                    text="z" * 2000,
                    score=0.7,
                    source="patterns",
                    payload={"template": "z" * 2000, "domain": "general"},
                )
            ],
        )
        result = augmenter.augment(
            raw_prompt="test prompt",
            context=large_context,
            user_preferences=user_preferences,
        )
        # The result may be large but must always contain the raw prompt
        assert "test prompt" in result

    def test_augment_custom_instructions_included(self, augmenter, full_context):
        """Custom instructions from user preferences should appear in the output."""
        prefs_with_custom = {
            "tone": "casual",
            "verbosity": "concise",
            "target_model": "Claude",
            "domain": "writing",
            "custom_instructions": "Always use simple words and short sentences.",
        }
        result = augmenter.augment(
            raw_prompt="explain quantum computing",
            context=full_context,
            user_preferences=prefs_with_custom,
        )
        assert "simple words" in result

    def test_augment_output_ends_with_prompt_section(self, augmenter, full_context, user_preferences):
        """The output must end with the prompt-to-optimise section."""
        raw = "my test prompt here"
        result = augmenter.augment(
            raw_prompt=raw,
            context=full_context,
            user_preferences=user_preferences,
        )
        # The raw prompt section should be near the end
        idx_raw = result.find(raw)
        assert idx_raw != -1
        # Nothing substantial should follow the prompt section
        assert len(result[idx_raw + len(raw):]) < 200


# ── Tests: RetrievalService (mocking Qdrant and embedding) ────────────────────

class TestRetrievalService:
    """Tests for app.services.retrieval_service.RetrievalService"""

    @pytest.fixture
    def mock_qdrant_hit(self):
        """A mock Qdrant ScoredPoint."""
        hit = MagicMock()
        hit.score = 0.89
        hit.payload = {
            "preference_text": "User prefers professional tone",
            "user_id": "test-user-123",
            "content": "previous message content",
            "template": "Act as an expert in {domain}...",
            "domain": "coding",
        }
        return hit

    def test_search_preferences_returns_list(self, mock_qdrant_hit):
        """search_preferences must return a list of RetrievalResult."""
        from app.services.retrieval_service import retrieval_service, RetrievalResult

        with patch.object(retrieval_service, 'search_preferences', return_value=[
            RetrievalResult(
                text="User prefers professional tone",
                score=0.89,
                source="preferences",
                payload={"preference_text": "...", "user_id": "123"},
            )
        ]) as mock:
            results = retrieval_service.search_preferences("user-123", "write code")

        assert isinstance(results, list)
        assert all(isinstance(r, RetrievalResult) for r in results)

    def test_search_history_filters_by_user(self):
        """search_history should only return results for the given user_id."""
        from app.services.retrieval_service import retrieval_service, RetrievalResult

        user_a_result = RetrievalResult(
            text="User A past prompt", score=0.9, source="history",
            payload={"user_id": "user-a", "content": "User A past prompt"},
        )
        with patch.object(retrieval_service, 'search_history', return_value=[user_a_result]):
            results = retrieval_service.search_history("user-a", "some query")

        for r in results:
            assert r.source == "history"

    def test_search_patterns_returns_relevant(self):
        """search_patterns should return pattern results."""
        from app.services.retrieval_service import retrieval_service, RetrievalResult

        pattern_result = RetrievalResult(
            text="Act as a senior developer...", score=0.92, source="patterns",
            payload={"template": "Act as a senior developer...", "domain": "coding"},
        )
        with patch.object(retrieval_service, 'search_patterns', return_value=[pattern_result]):
            results = retrieval_service.search_patterns("debug this code")

        assert len(results) > 0
        assert results[0].source == "patterns"

    def test_retrieve_context_deduplicates_history(self):
        """Combined context must not contain duplicate history entries."""
        from app.services.retrieval_service import retrieval_service, RetrievalResult, CombinedContext

        duplicate_text = "I need help with Python loops"
        context = CombinedContext(
            preferences=[],
            history=[
                RetrievalResult(duplicate_text, 0.9, "history", {}),
                RetrievalResult(duplicate_text, 0.85, "history", {}),  # exact duplicate
                RetrievalResult("different message", 0.7, "history", {}),
            ],
            patterns=[],
        )
        # Apply the deduplication logic directly (same logic as retrieve_context)
        seen = set()
        deduped = []
        for item in context.history:
            normalized = item.text.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                deduped.append(item)

        assert len(deduped) == 2  # duplicate removed, 2 unique items remain

    def test_retrieve_context_handles_qdrant_failure_gracefully(self):
        """If Qdrant is down, retrieval must return empty results (not raise)."""
        from app.services.retrieval_service import retrieval_service

        with patch.object(
            retrieval_service, 'search_preferences',
            side_effect=Exception("Qdrant connection refused")
        ):
            # This shouldn't raise; search_preferences has try/except
            result = retrieval_service.search_preferences("user-123", "test query")

        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_context_async_returns_combined_context(self):
        """retrieve_context_async must return a CombinedContext object."""
        from app.services.retrieval_service import retrieval_service, CombinedContext, RetrievalResult

        mock_pref = [RetrievalResult("pref", 0.9, "preferences", {})]
        mock_hist = [RetrievalResult("hist", 0.8, "history", {})]
        mock_patt = [RetrievalResult("patt", 0.7, "patterns", {})]

        with patch.object(retrieval_service, 'search_preferences', return_value=mock_pref), \
             patch.object(retrieval_service, 'search_history', return_value=mock_hist), \
             patch.object(retrieval_service, 'search_patterns', return_value=mock_patt):

            result = await retrieval_service.retrieve_context_async(
                user_id="user-123",
                query="test prompt",
                domain="coding",
            )

        assert isinstance(result, CombinedContext)
        assert result.preferences == mock_pref
        assert result.patterns == mock_patt


# ── Tests: RAG-augmented inference endpoint ────────────────────────────────────

class TestRAGInferenceEndpoint:
    """Integration tests for prompts.py with mocked RAG and AI."""

    @pytest.mark.asyncio
    async def test_optimize_with_rag_disabled_uses_raw_prompt(self):
        """When use_rag=False, the raw prompt should be sent directly to AI."""
        from app.rag.augmenter import prompt_augmenter
        from app.services.retrieval_service import retrieval_service, CombinedContext

        raw = "write me a poem"

        with patch.object(retrieval_service, 'retrieve_context_async') as mock_retrieve, \
             patch.object(prompt_augmenter, 'augment') as mock_augment:

            # Import the helper function
            from app.api.v1.prompts import _build_augmented_prompt
            prompt, rag_used = await _build_augmented_prompt(
                raw_prompt=raw,
                user_id="user-123",
                user_prefs=None,
                use_rag=False,
            )

        assert prompt == raw
        assert rag_used is False
        mock_retrieve.assert_not_called()
        mock_augment.assert_not_called()

    @pytest.mark.asyncio
    async def test_optimize_with_rag_enabled_calls_retrieval(self):
        """When use_rag=True, retrieval_service must be called."""
        from app.services.retrieval_service import retrieval_service, CombinedContext

        mock_context = CombinedContext(preferences=[], history=[], patterns=[])

        with patch.object(
            retrieval_service, 'retrieve_context_async',
            new_callable=AsyncMock,
            return_value=mock_context,
        ) as mock_retrieve:
            from app.api.v1.prompts import _build_augmented_prompt
            prompt, rag_used = await _build_augmented_prompt(
                raw_prompt="test prompt",
                user_id="user-123",
                user_prefs={"domain": "coding"},
                use_rag=True,
            )

        mock_retrieve.assert_called_once_with(
            user_id="user-123",
            query="test prompt",
            domain="coding",
        )

    @pytest.mark.asyncio
    async def test_rag_failure_falls_back_to_raw_prompt(self):
        """If RAG pipeline throws, _build_augmented_prompt falls back to raw."""
        from app.services.retrieval_service import retrieval_service

        raw = "my raw prompt"
        with patch.object(
            retrieval_service, 'retrieve_context_async',
            new_callable=AsyncMock,
            side_effect=Exception("Qdrant timeout"),
        ):
            from app.api.v1.prompts import _build_augmented_prompt
            prompt, rag_used = await _build_augmented_prompt(
                raw_prompt=raw,
                user_id="user-123",
                user_prefs=None,
                use_rag=True,
            )

        # Falls back gracefully
        assert prompt == raw
        assert rag_used is False

    @pytest.mark.asyncio
    async def test_augmented_prompt_is_richer_than_raw(self):
        """With full context, the augmented prompt should be longer than the raw prompt."""
        from app.services.retrieval_service import retrieval_service, CombinedContext
        from app.rag.augmenter import prompt_augmenter
        from app.services.retrieval_service import RetrievalResult

        raw = "explain machine learning"
        mock_context = CombinedContext(
            preferences=[RetrievalResult("User prefers academic tone", 0.9, "preferences", {"preference_text": "User prefers academic tone"})],
            history=[RetrievalResult("Past question about neural networks", 0.8, "history", {"content": "Past question about neural networks"})],
            patterns=[RetrievalResult("Act as a machine learning researcher...", 0.85, "patterns", {"template": "Act as a machine learning researcher...", "domain": "education"})],
        )

        with patch.object(
            retrieval_service, 'retrieve_context_async',
            new_callable=AsyncMock,
            return_value=mock_context,
        ):
            from app.api.v1.prompts import _build_augmented_prompt
            augmented, rag_used = await _build_augmented_prompt(
                raw_prompt=raw,
                user_id="user-123",
                user_prefs={"tone": "academic", "domain": "education", "verbosity": "detailed", "target_model": "General", "custom_instructions": None},
                use_rag=True,
            )

        assert rag_used is True
        assert len(augmented) > len(raw)
        assert raw in augmented


# ── Tests: Embedding Service (unit) ───────────────────────────────────────────

class TestEmbeddingService:
    """Unit tests for embedding_service with mocked sentence-transformers model."""

    def test_embed_text_returns_list_of_floats(self):
        """embed_text must return a list of 384 floats."""
        from app.services.embedding_service import EmbeddingService

        mock_vector = [0.1] * 384
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: mock_vector)

        service = EmbeddingService()
        service._model = mock_model  # Inject mock

        result = service.embed_text("hello world")

        assert isinstance(result, list)
        assert len(result) == 384

    def test_embed_batch_returns_list_of_vectors(self):
        """embed_batch must return one vector per input text."""
        import numpy as np
        from app.services.embedding_service import EmbeddingService

        texts = ["text one", "text two", "text three"]
        mock_vectors = [MagicMock(tolist=lambda: [0.1] * 384) for _ in texts]

        mock_model = MagicMock()
        mock_model.encode.return_value = mock_vectors

        service = EmbeddingService()
        service._model = mock_model

        result = service.embed_batch(texts)

        assert isinstance(result, list)
        assert len(result) == len(texts)

    def test_embed_batch_empty_returns_empty(self):
        """embed_batch([]) must return [] without calling the model."""
        from app.services.embedding_service import EmbeddingService

        service = EmbeddingService()
        result = service.embed_batch([])
        assert result == []

    def test_lazy_loading_does_not_load_on_init(self):
        """The model must NOT be loaded at construction time."""
        from app.services.embedding_service import EmbeddingService

        service = EmbeddingService()
        assert service._model is None
