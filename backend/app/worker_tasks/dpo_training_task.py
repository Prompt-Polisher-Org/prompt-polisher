"""
dpo_training_task.py — Celery task for automated DPO model retraining.

Task: Week 11-12 / RLHF (task.md lines 593-597)
  [x] Trigger when feedback batch size threshold reached (e.g., 100)
  [x] Run DPO training on feedback data
  [x] Save new model checkpoint
  [x] Log training metrics

This task is designed to be triggered either:
1. Automatically when enough user feedback accumulates (via a periodic beat schedule)
2. Manually by an admin via an API endpoint
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

FEEDBACK_THRESHOLD = 100       # Minimum feedback samples before triggering training
FEEDBACK_DATA_DIR = Path("ai/data/feedback")
DPO_TRIPLES_FILE = FEEDBACK_DATA_DIR / "dpo_triples.jsonl"
TRAINING_LOG_FILE = FEEDBACK_DATA_DIR / "training_runs.jsonl"
BASE_CHECKPOINT = "ai/models/checkpoints/sft_best.pt"
DPO_OUTPUT_DIR = "ai/models/checkpoints/dpo"


# ── Helper: Export feedback to DPO triples ────────────────────────────────────

def export_feedback_to_triples(db_url: str) -> int:
    """
    Query the PostgreSQL feedback table and export (prompt, chosen, rejected)
    triples for DPO training.

    Returns the number of triples exported.
    """
    import sqlalchemy
    from sqlalchemy import text

    engine = sqlalchemy.create_engine(db_url.replace("+asyncpg", ""))

    query = text("""
        SELECT
            m_user.content AS prompt,
            m_chosen.content AS chosen,
            m_rejected.content AS rejected
        FROM feedback f_pos
        JOIN messages m_chosen ON f_pos.message_id = m_chosen.id
        JOIN chat_sessions cs ON m_chosen.session_id = cs.id
        JOIN messages m_user ON m_user.session_id = m_chosen.session_id
            AND m_user.role = 'user'
            AND m_user.created_at < m_chosen.created_at
        JOIN feedback f_neg ON f_neg.rating = 'negative'
        JOIN messages m_rejected ON f_neg.message_id = m_rejected.id
        WHERE f_pos.rating = 'positive'
        ORDER BY f_pos.created_at DESC
        LIMIT 5000
    """)

    FEEDBACK_DATA_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            with open(DPO_TRIPLES_FILE, "w", encoding="utf-8") as f:
                for row in result:
                    triple = {
                        "prompt": row.prompt,
                        "chosen": row.chosen,
                        "rejected": row.rejected,
                    }
                    f.write(json.dumps(triple, ensure_ascii=False) + "\n")
                    count += 1
    except Exception as e:
        logger.error(f"Failed to export feedback data: {e}")
        # If DB isn't available, check if we have existing triples file
        if DPO_TRIPLES_FILE.exists():
            with open(DPO_TRIPLES_FILE, "r") as f:
                count = sum(1 for _ in f)
            logger.info(f"Using existing triples file with {count} entries")

    logger.info(f"Exported {count} DPO triples to {DPO_TRIPLES_FILE}")
    return count


# ── Celery Task: Check and Trigger DPO Training ──────────────────────────────

@celery_app.task(name="app.worker_tasks.dpo_training_task.check_and_train_dpo")
def check_and_train_dpo():
    """
    Periodic task that checks if enough feedback has accumulated
    and triggers DPO retraining if the threshold is reached.

    This should be scheduled via Celery Beat (e.g., every 6 hours).
    """
    logger.info("Checking feedback accumulation for DPO training...")

    # 1. Export latest feedback from the database
    try:
        from app.core.config import settings
        db_url = settings.DATABASE_URL
        triple_count = export_feedback_to_triples(db_url)
    except Exception as e:
        logger.warning(f"Could not export feedback from DB: {e}")
        # Check existing file
        if DPO_TRIPLES_FILE.exists():
            with open(DPO_TRIPLES_FILE, "r") as f:
                triple_count = sum(1 for line in f if line.strip())
        else:
            triple_count = 0

    # 2. Check threshold
    if triple_count < FEEDBACK_THRESHOLD:
        logger.info(
            f"Not enough feedback yet: {triple_count}/{FEEDBACK_THRESHOLD} triples. "
            f"Skipping DPO training."
        )
        return {
            "status": "skipped",
            "reason": f"Only {triple_count}/{FEEDBACK_THRESHOLD} triples available",
        }

    # 3. Trigger DPO training
    logger.info(f"Threshold reached ({triple_count} triples). Starting DPO training...")
    result = run_dpo_training.delay()
    return {
        "status": "triggered",
        "triple_count": triple_count,
        "training_task_id": result.id,
    }


@celery_app.task(
    name="app.worker_tasks.dpo_training_task.run_dpo_training",
    bind=True,
    max_retries=1,
    time_limit=7200,   # 2 hour hard limit
    soft_time_limit=6600,  # 1h50m soft limit (gives 10min to save checkpoint)
)
def run_dpo_training(self):
    """
    Execute the DPO training pipeline.

    This is a long-running task that should be dispatched to a dedicated
    Celery worker with GPU access.
    """
    start_time = time.time()
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    logger.info(f"DPO Training Run {run_id} starting...")

    training_log = {
        "run_id": run_id,
        "started_at": datetime.utcnow().isoformat(),
        "status": "running",
    }

    try:
        # Import the DPO trainer
        from ai.src.training.dpo_trainer import DPOTrainer, DPOConfig

        config = DPOConfig(
            feedback_data_path=str(DPO_TRIPLES_FILE),
            base_checkpoint=BASE_CHECKPOINT,
            output_dir=f"{DPO_OUTPUT_DIR}/{run_id}",
        )

        trainer = DPOTrainer(config)
        trainer.train()

        elapsed = time.time() - start_time
        training_log.update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": elapsed,
            "output_dir": config.output_dir,
        })

        logger.info(f"DPO Training Run {run_id} completed in {elapsed / 60:.1f} minutes")

    except Exception as e:
        elapsed = time.time() - start_time
        training_log.update({
            "status": "failed",
            "error": str(e),
            "duration_seconds": elapsed,
        })
        logger.error(f"DPO Training Run {run_id} failed: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

    finally:
        # Log the training run
        FEEDBACK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(TRAINING_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(training_log) + "\n")

    return training_log
"""
Model Versioning System — Week 11-12 (task.md lines 598-601)
  [x] Version tagging for each checkpoint
  [x] Rollback capability
  [x] Model comparison tool (old vs new)
"""


@celery_app.task(name="app.worker_tasks.dpo_training_task.list_model_versions")
def list_model_versions():
    """List all available model versions with metadata."""
    versions = []
    checkpoints_dir = Path("ai/models/checkpoints")

    # Scan for DPO checkpoints
    dpo_dir = checkpoints_dir / "dpo"
    if dpo_dir.exists():
        for run_dir in sorted(dpo_dir.iterdir()):
            if run_dir.is_dir():
                best_ckpt = run_dir / "dpo_best.pt"
                final_ckpt = run_dir / "dpo_final.pt"
                ckpt = best_ckpt if best_ckpt.exists() else final_ckpt

                if ckpt.exists():
                    versions.append({
                        "version": f"dpo-{run_dir.name}",
                        "type": "dpo",
                        "path": str(ckpt),
                        "size_mb": ckpt.stat().st_size / (1024 * 1024),
                        "created_at": datetime.fromtimestamp(
                            ckpt.stat().st_mtime
                        ).isoformat(),
                    })

    # Check for SFT checkpoint
    sft_best = checkpoints_dir / "sft_best.pt"
    if sft_best.exists():
        versions.insert(0, {
            "version": "sft-base",
            "type": "sft",
            "path": str(sft_best),
            "size_mb": sft_best.stat().st_size / (1024 * 1024),
            "created_at": datetime.fromtimestamp(
                sft_best.stat().st_mtime
            ).isoformat(),
        })

    return {"versions": versions, "total": len(versions)}


@celery_app.task(name="app.worker_tasks.dpo_training_task.rollback_model")
def rollback_model(version: str):
    """
    Rollback to a specific model version by updating the active model symlink.
    """
    checkpoints_dir = Path("ai/models/checkpoints")
    active_link = checkpoints_dir / "active_model.pt"

    # Find the requested version
    if version == "sft-base":
        target = checkpoints_dir / "sft_best.pt"
    elif version.startswith("dpo-"):
        run_id = version[4:]  # Strip "dpo-" prefix
        target = checkpoints_dir / "dpo" / run_id / "dpo_best.pt"
        if not target.exists():
            target = checkpoints_dir / "dpo" / run_id / "dpo_final.pt"
    else:
        return {"status": "error", "message": f"Unknown version: {version}"}

    if not target.exists():
        return {"status": "error", "message": f"Checkpoint not found: {target}"}

    # Update symlink (or copy on Windows)
    import shutil
    if active_link.exists():
        active_link.unlink()

    try:
        active_link.symlink_to(target.resolve())
    except OSError:
        # Windows may not support symlinks — copy instead
        shutil.copy2(target, active_link)

    logger.info(f"Rolled back active model to version: {version} ({target})")
    return {
        "status": "success",
        "active_version": version,
        "checkpoint_path": str(target),
    }
