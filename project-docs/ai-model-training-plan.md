# 🤖 AI Model Training Plan: Prompt Polisher

> **Timeline**: Parallel to Week 5-6 | **Owner**: `🤖 AI` Team Member
> **Status**: 📋 Planned

---

## The Concept: What are we doing?

We are not building a brain from scratch. We are taking an already smart brain (an Open-Source model like *Llama-3* that knows English and reasoning) and sending it to "Prompt Engineering Bootcamp". We do this by showing it thousands of examples until it learns the pattern.

---

## Phase 1: Data Collection & Preparation
*Estimated Time: 1-2 Days*

The model only learns what you show it. If we show it garbage, it learns garbage. We need to create a "Textbook" for the model to study.

1. **Create the Dataset**: We will write a script to create a `.jsonl` (JSON Lines) file containing pairs of bad prompts and perfect prompts.
2. **Format the Data**: We will format these pairs into a "Conversation" format that the model understands, using standard chat templates.
   ```json
   {
     "messages": [
       {"role": "system", "content": "You are an expert prompt engineer. Enhance the user's prompt."},
       {"role": "user", "content": "write a snake game"},
       {"role": "assistant", "content": "Act as a Senior Python Game Developer. Write a complete, fully functional Snake game using the Pygame library. Ensure the code is modular..."}
     ]
   }
   ```

## Phase 2: Choosing the Base Model
*Estimated Time: 1 Day*

We need to pick the "Student" that will read our textbook. We will use the Hugging Face library to download a pre-trained model.

1. **Select Model**: We will likely use `Meta-Llama-3-8B-Instruct` or `Mistral-7B-Instruct`. These are small enough to train on a single graphics card but smart enough to generate amazing results.
2. **Quantization (Shrinking the model)**: An 8-Billion parameter model is huge. We will use a technique called **4-bit Quantization (bitsandbytes)** to compress the model so it fits into your computer's RAM/VRAM without losing its intelligence.

## Phase 3: Setting up the Training Environment (QLoRA)
*Estimated Time: 1 Day*

Training a whole model requires supercomputers. Instead, we use a trick called **QLoRA (Quantized Low-Rank Adaptation)**.

1. **How it works**: Instead of opening up the model's brain and changing everything, we "freeze" the brain and attach a tiny, trainable "adapter" module to it.
2. **The Script**: We will write a Python script using the `TRL` (Transformer Reinforcement Learning) library. We will configure it to only train our tiny adapter on our dataset.

## Phase 4: Training (Supervised Fine-Tuning - SFT)
*Estimated Time: 1-3 Days (mostly waiting)*

This is where the actual machine learning happens.

1. **Start the Loop**: We run our Python script. The script feeds our JSON examples to the model one by one.
2. **Loss Monitoring**: The model makes a guess, compares it to our perfect prompt, calculates how wrong it was (this is called "Loss"), and updates its adapter weights to be less wrong next time.
3. **Wait**: We let this run for a few hours (or days, depending on your GPU) until the "Loss" number gets very low and stops dropping.

## Phase 5: Testing & Merging
*Estimated Time: 1 Day*

1. **Chat Test**: We load the base model and attach our newly trained adapter. We type in a terrible prompt and see if it outputs a beautifully polished prompt.
2. **Merge Weights**: Once we are happy, we mathematically merge the tiny adapter permanently into the base model.
3. **Export**: We save this new, merged model to your disk as the final `Prompt-Polisher-v1` model!

---

## AI Verification Plan
We will verify success by passing 10 "blind" bad prompts to the new model and having the team manually grade if the rewritten prompts are high quality and ready to be used in your web application.
