"""
services/embedding_service.py — Sentence embedding service for RAG.

Task: Week 7-8 / Embedding & Vector Database (task.md lines 377-381)
  [x] Load sentence-transformers/all-MiniLM-L6-v2
  [x] embed_text(text: str) -> List[float] method
  [x] embed_batch(texts: List[str]) -> List[List[float]] method
  [x] Lazy model loading (load once, reuse)
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

# The model produces 384-dimensional vectors and runs fully on CPU.
# It is small (~90MB) and fast enough for our latency requirements.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Singleton-style service that lazily loads the sentence-transformer model
    on first use and reuses it for all subsequent calls.

    Using lazy loading keeps startup time fast and avoids loading the model
    if RAG features are not used in a given request.
    """

    def __init__(self):
        self._model = None  # Not loaded yet

    def _load_model(self):
        """Load the model into memory on first call. Thread-safe in asyncio context."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # deferred import
            logger.info(f"Loading embedding model: {MODEL_NAME}")
            self._model = SentenceTransformer(MODEL_NAME)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string into a 384-dimensional vector.

        Args:
            text: Any string (prompt, preference description, etc.)

        Returns:
            A list of 384 floats representing the semantic meaning of the text.
        """
        model = self._load_model()
        # convert_to_list=True ensures we get plain Python floats, not numpy
        vector = model.encode(text, convert_to_tensor=False, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts efficiently.

        Batching is much faster than calling embed_text() in a loop because
        the model can process multiple texts in one forward pass.

        Args:
            texts: A list of strings to embed.

        Returns:
            A list of 384-dim vectors, one per input text.
        """
        if not texts:
            return []
        model = self._load_model()
        vectors = model.encode(
            texts,
            batch_size=64,
            convert_to_tensor=False,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]


# Module-level singleton — imported by other services
embedding_service = EmbeddingService()
