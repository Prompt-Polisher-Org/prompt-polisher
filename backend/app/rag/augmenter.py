"""
rag/augmenter.py — Builds augmented prompts by injecting RAG context.

Task: Week 7-8 / RAG Integration (task.md lines 400-409)
  [x] Construct augmented system prompt template
  [x] Inject user preferences into prompt
  [x] Inject relevant chat history into prompt
  [x] Inject prompt patterns into prompt
  [x] Token budget management (don't exceed context window)
"""
import logging
from typing import Optional

from app.services.retrieval_service import CombinedContext

logger = logging.getLogger(__name__)

# ── Token budget constants ────────────────────────────────────────────────────
# Our model's context window is 1024-2048 tokens.
# Reserve ~512 tokens for the raw user prompt + generated response.
# That leaves ~512-1024 tokens for RAG context.
# We use a conservative character budget (1 token ≈ 4 chars for English text).
MAX_CONTEXT_CHARS = 1800     # ~450 tokens of context
MAX_HISTORY_ITEMS = 3        # At most 3 history snippets
MAX_PATTERN_ITEMS = 2        # At most 2 prompt patterns


class PromptAugmenter:
    """
    Builds an enriched prompt by combining:
      1. User preferences (tone, domain, verbosity, custom instructions)
      2. Relevant past conversations from this user
      3. Proven prompt templates that match the user's domain/query

    The final augmented prompt is sent to the AI model instead of the raw user text.
    This is the core of RAG-based personalisation.
    """

    def augment(
        self,
        raw_prompt: str,
        context: CombinedContext,
        user_preferences: Optional[dict] = None,
    ) -> str:
        """
        Construct the full augmented prompt string.

        Args:
            raw_prompt:       The user's original, unoptimised prompt text.
            context:          Retrieved context from all 3 Qdrant collections.
            user_preferences: Optional dict with keys: tone, verbosity, target_model,
                              domain, custom_instructions (from the DB preferences row).

        Returns:
            A single string that will be sent to the AI model as the full input.
            The model is trained to read this format and produce an optimised prompt.
        """
        sections: list[str] = []
        chars_used = 0

        # ── Section 1: Task instruction (always present) ──────────────────
        task_header = (
            "You are an expert prompt engineer. "
            "Your job is to transform the user's rough prompt into a clear, "
            "structured, and highly effective prompt for an AI model.\n"
        )
        sections.append(task_header)
        chars_used += len(task_header)

        # ── Section 2: User preference context ───────────────────────────
        pref_section = self._build_preference_section(context, user_preferences)
        if pref_section and chars_used + len(pref_section) < MAX_CONTEXT_CHARS:
            sections.append(pref_section)
            chars_used += len(pref_section)

        # ── Section 3: Relevant chat history ─────────────────────────────
        history_section = self._build_history_section(context)
        if history_section and chars_used + len(history_section) < MAX_CONTEXT_CHARS:
            sections.append(history_section)
            chars_used += len(history_section)

        # ── Section 4: Prompt patterns / templates ────────────────────────
        patterns_section = self._build_patterns_section(context)
        if patterns_section and chars_used + len(patterns_section) < MAX_CONTEXT_CHARS:
            sections.append(patterns_section)
            chars_used += len(patterns_section)

        # ── Section 5: The raw user prompt (always last) ──────────────────
        prompt_section = (
            "=== USER PROMPT TO OPTIMISE ===\n"
            f"{raw_prompt.strip()}\n\n"
            "=== OPTIMISED PROMPT ===\n"
        )
        sections.append(prompt_section)

        augmented = "\n".join(sections)

        logger.debug(
            f"Augmented prompt built: {len(augmented)} chars, "
            f"prefs={len(context.preferences)}, "
            f"history={len(context.history)}, "
            f"patterns={len(context.patterns)}"
        )
        return augmented

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_preference_section(
        self,
        context: CombinedContext,
        user_preferences: Optional[dict],
    ) -> str:
        """Build the user preference context block."""
        lines: list[str] = []

        # Prefer the richer DB preferences dict if provided
        if user_preferences:
            tone = user_preferences.get("tone", "professional")
            verbosity = user_preferences.get("verbosity", "balanced")
            target_model = user_preferences.get("target_model", "General")
            domain = user_preferences.get("domain", "general")
            custom = user_preferences.get("custom_instructions") or ""

            lines.append("=== USER PREFERENCES ===")
            lines.append(
                f"- Tone: {tone}  |  Verbosity: {verbosity}  "
                f"|  Domain: {domain}  |  Target AI: {target_model}"
            )
            if custom:
                lines.append(f"- Custom instructions: {custom}")

        # Fall back to Qdrant retrieved preference text
        elif context.preferences:
            pref_text = context.preferences[0].text
            lines.append("=== USER PREFERENCES ===")
            lines.append(pref_text)

        if not lines:
            return ""

        lines.append("")  # blank separator
        return "\n".join(lines)

    def _build_history_section(self, context: CombinedContext) -> str:
        """Build the relevant chat history block."""
        items = context.history[:MAX_HISTORY_ITEMS]
        if not items:
            return ""

        lines = ["=== RELEVANT PAST CONVERSATIONS ==="]
        for i, item in enumerate(items, 1):
            # Truncate each history item to 300 chars to respect token budget
            snippet = item.text[:300].strip()
            if len(item.text) > 300:
                snippet += "..."
            lines.append(f"{i}. {snippet}")

        lines.append("")
        return "\n".join(lines)

    def _build_patterns_section(self, context: CombinedContext) -> str:
        """Build the prompt patterns / templates block."""
        items = context.patterns[:MAX_PATTERN_ITEMS]
        if not items:
            return ""

        lines = ["=== PROVEN PROMPT PATTERNS ==="]
        for i, item in enumerate(items, 1):
            domain = item.payload.get("domain", "general")
            # Truncate each pattern to 400 chars
            template = item.text[:400].strip()
            if len(item.text) > 400:
                template += "..."
            lines.append(f"{i}. [{domain.upper()}] {template}")

        lines.append("")
        return "\n".join(lines)


# Module-level singleton
prompt_augmenter = PromptAugmenter()
