"""
api/v1/ab_testing.py — A/B Testing API endpoints.

Endpoints:
  POST   /api/v1/ab/experiments          — Create a new experiment
  GET    /api/v1/ab/experiments           — List all experiments
  GET    /api/v1/ab/experiments/{id}/stats — Get comparison stats
  POST   /api/v1/ab/results/{id}/rate     — Rate an A/B result
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.ab_experiment import ABExperiment, ABResult
from app.services.ab_testing_service import ab_testing_service

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateExperimentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model_a: str = Field(..., description="Checkpoint path or version tag for model A")
    model_b: str = Field(..., description="Checkpoint path or version tag for model B")
    traffic_pct_b: int = Field(50, ge=0, le=100, description="% of traffic to model B")


class ExperimentResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_a: str
    model_b: str
    traffic_pct_b: int
    is_active: bool


class RateRequest(BaseModel):
    rating: int = Field(..., description="1 for thumbs up, -1 for thumbs down")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/experiments", response_model=ExperimentResponse)
async def create_experiment(
    req: CreateExperimentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new A/B test experiment."""
    experiment = ABExperiment(
        name=req.name,
        description=req.description,
        model_a=req.model_a,
        model_b=req.model_b,
        traffic_pct_b=req.traffic_pct_b,
    )
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)
    return experiment


@router.get("/experiments")
async def list_experiments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all A/B experiments."""
    result = await db.execute(
        select(ABExperiment).order_by(ABExperiment.created_at.desc())
    )
    experiments = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "model_a": e.model_a,
            "model_b": e.model_b,
            "traffic_pct_b": e.traffic_pct_b,
            "is_active": e.is_active,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in experiments
    ]


@router.get("/experiments/{experiment_id}/stats")
async def get_experiment_stats(
    experiment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comparison statistics for an A/B experiment."""
    experiment = await db.get(ABExperiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    stats = await ab_testing_service.get_experiment_stats(db, experiment_id)
    return {
        "experiment": {
            "id": str(experiment.id),
            "name": experiment.name,
            "model_a": experiment.model_a,
            "model_b": experiment.model_b,
        },
        "stats": stats,
    }


@router.post("/results/{result_id}/rate")
async def rate_ab_result(
    result_id: uuid.UUID,
    req: RateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rate an A/B test result (thumbs up / thumbs down)."""
    if req.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 or -1")

    result = await db.get(ABResult, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="A/B result not found")

    await ab_testing_service.record_rating(db, result_id, req.rating)
    return {"status": "ok", "result_id": str(result_id), "rating": req.rating}
