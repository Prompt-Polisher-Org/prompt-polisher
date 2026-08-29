import asyncio
import json
import os
import sys

# Add backend directory to sys.path so we can import app modules when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import SessionLocal
from app.models.feedback import Feedback
from app.models.message import Message
from app.models.session import ChatSession  # Required to resolve SQLAlchemy string relationship on Message

async def export_dpo_dataset(output_path: str = "dpo_dataset.jsonl"):
    """
    Exports user feedback from the PostgreSQL database into a JSONL format
    suitable for Direct Preference Optimization (DPO) fine-tuning.
    
    Format: {"prompt": "...", "chosen": "...", "rejected": "..."}
    """
    print(f"Exporting DPO feedback data to {output_path}...")
    
    dataset = []
    
    async with SessionLocal() as db:
        # Fetch all feedback with their associated messages using a standard join
        stmt = (
            select(Feedback, Message)
            .join(Message, Feedback.message_id == Message.id)
            .order_by(Feedback.created_at.desc())
        )
        
        result = await db.execute(stmt)
        # Result contains tuples of (Feedback, Message)
        rows = result.all()

        # Group by raw_content (the prompt)
        grouped_by_prompt = {}
        for fb, msg in rows:
            # Skip if there's no message or no polished content
            if not msg or not msg.polished_content:
                continue
            
            prompt = msg.raw_content
            if prompt not in grouped_by_prompt:
                grouped_by_prompt[prompt] = {"chosen": [], "rejected": []}
                
            if fb.rating == 1:
                grouped_by_prompt[prompt]["chosen"].append(msg.polished_content)
            elif fb.rating == -1:
                grouped_by_prompt[prompt]["rejected"].append(msg.polished_content)

        for prompt, interactions in grouped_by_prompt.items():
            chosen_list = interactions["chosen"]
            rejected_list = interactions["rejected"]
            
            # Scenario 1: We have both positive and negative feedback for the same prompt
            if chosen_list and rejected_list:
                # Create pairs (zip stops at the shortest list)
                for c, r in zip(chosen_list, rejected_list):
                    dataset.append({
                        "prompt": prompt,
                        "chosen": c,
                        "rejected": r
                    })
            
            # Scenario 2: We only have positive feedback
            # Fallback: Treat the raw, unpolished prompt as the "rejected" baseline
            # This teaches the model that polishing is strictly better than doing nothing.
            elif chosen_list:
                for c in chosen_list:
                    if c != prompt:
                        dataset.append({
                            "prompt": prompt,
                            "chosen": c,
                            "rejected": prompt
                        })

    if not dataset:
        print("\u26a0\ufe0f No valid DPO pairs found in the database. Ensure you have submitted thumbs up/down feedback on the frontend!")
        return

    # Write to JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"\u2705 Successfully exported {len(dataset)} DPO training pairs!")
    print(f"You can now upload '{output_path}' to Google Colab for DPO fine-tuning.")

if __name__ == "__main__":
    # Default output path is in the backend/ directory
    output_file = os.path.join(os.path.dirname(__file__), "../../dpo_dataset.jsonl")
    asyncio.run(export_dpo_dataset(output_file))
