"""
services/ab_testing_service.py — A/B Testing service for model comparison.

Responsibilities:
  1. Determine which model variant (A or B) to serve for a given user.
  2. Record the result of each inference with the variant tag.
  3. Aggregate satisfaction metrics per variant for comparison.
"""
import random
import uuid
import logging
from typing import Optional

from sqlalchemy import select, func as sqla_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ab_experiment import ABExperiment, ABResult

logger = logging.getLogger("prompt_polisher")


class ABTestingService:
    """Manages A/B test experiment lifecycle."""

    async def get_active_experiment(self, db: AsyncSession) -> Optional[ABExperiment]:
        """Return the currently active A/B experiment, if any."""
        result = await db.execute(
            select(ABExperiment).where(ABExperiment.is_active == True).limit(1)
        )
        return result.scalar_one_or_none()

    def assign_variant(self, experiment: ABExperiment, user_id: uuid.UUID) -> str:
        """
        Assign a variant (A or B) to a user for this experiment.

        Uses a deterministic hash of (experiment_id + user_id) so the same
        user always gets the same variant within an experiment. This prevents
        variant flickering across requests.
        """
        combined = f"{experiment.id}:{user_id}"
        hash_value = hash(combined) % 100  # 0-99

        if hash_value < experiment.traffic_pct_b:
            return "B"
        return "A"

    def get_model_for_variant(self, experiment: ABExperiment, variant: str) -> str:
        """Return the model identifier for the given variant."""
        if variant == "B":
            return experiment.model_b
        return experiment.model_a

    async def record_result(
        self,
        db: AsyncSession,
        experiment_id: uuid.UUID,
        user_id: uuid.UUID,
        variant: str,
        model_version: str,
        prompt: str,
        response: Optional[str] = None,
        latency_ms: Optional[float] = None,
        tokens_generated: Optional[int] = None,
    ) -> ABResult:
        """Record an individual A/B test inference result."""
        result = ABResult(
            experiment_id=experiment_id,
            user_id=user_id,
            variant=variant,
            model_version=model_version,
            prompt=prompt,
            response=response,
            latency_ms=latency_ms,
            tokens_generated=tokens_generated,
        )
        db.add(result)
        await db.commit()
        await db.refresh(result)

        logger.info(
            "ab_result_recorded",
            extra={
                "experiment_id": str(experiment_id),
                "variant": variant,
                "model_version": model_version,
                "latency_ms": latency_ms,
            },
        )
        return result

    async def record_rating(
        self, db: AsyncSession, result_id: uuid.UUID, rating: int
    ):
        """Attach a user rating (1 or -1) to an existing A/B result."""
        result = await db.get(ABResult, result_id)
        if result:
            result.rating = rating
            await db.commit()

    async def get_experiment_stats(
        self, db: AsyncSession, experiment_id: uuid.UUID
    ) -> dict:
        """
        Aggregate and compare metrics for variant A vs B.

        Returns:
            {
                "A": { "total": N, "avg_latency_ms": X, "thumbs_up": Y, "thumbs_down": Z, "satisfaction": P% },
                "B": { ... },
                "winner": "A" | "B" | "tie"
            }
        """
        stats = {}
        for variant in ("A", "B"):
            # Total count
            count_q = await db.execute(
                select(sqla_func.count(ABResult.id)).where(
                    ABResult.experiment_id == experiment_id,
                    ABResult.variant == variant,
                )
            )
            total = count_q.scalar() or 0

            # Average latency
            latency_q = await db.execute(
                select(sqla_func.avg(ABResult.latency_ms)).where(
                    ABResult.experiment_id == experiment_id,
                    ABResult.variant == variant,
                    ABResult.latency_ms.isnot(None),
                )
            )
            avg_latency = round(latency_q.scalar() or 0, 2)

            # Thumbs up / down
            up_q = await db.execute(
                select(sqla_func.count(ABResult.id)).where(
                    ABResult.experiment_id == experiment_id,
                    ABResult.variant == variant,
                    ABResult.rating == 1,
                )
            )
            thumbs_up = up_q.scalar() or 0

            down_q = await db.execute(
                select(sqla_func.count(ABResult.id)).where(
                    ABResult.experiment_id == experiment_id,
                    ABResult.variant == variant,
                    ABResult.rating == -1,
                )
            )
            thumbs_down = down_q.scalar() or 0

            rated_total = thumbs_up + thumbs_down
            satisfaction = round((thumbs_up / rated_total) * 100, 1) if rated_total > 0 else 0.0

            stats[variant] = {
                "total": total,
                "avg_latency_ms": avg_latency,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "satisfaction_pct": satisfaction,
            }

        # Determine winner
        sat_a = stats["A"]["satisfaction_pct"]
        sat_b = stats["B"]["satisfaction_pct"]
        if sat_a > sat_b:
            winner = "A"
        elif sat_b > sat_a:
            winner = "B"
        else:
            winner = "tie"

        return {**stats, "winner": winner}


ab_testing_service = ABTestingService()
