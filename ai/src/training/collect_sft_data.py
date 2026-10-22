"""
collect_sft_data.py -- Collect and curate SFT dataset for prompt optimization.

Produces high-quality (bad_prompt -> optimized_prompt) pairs from:
  1. Prompt_Preference_Dataset (HuggingFace, 30K) -- GPT-4 prompt rewrites (PRIMARY)
  2. Local MATH dataset (FY_dataset/train.csv) -- LaTeX math prompt polishing
  3. Dolly-15k (HuggingFace) -- general instruction polishing (template-based)
  4. CodeAlpaca-20k (HuggingFace) -- code prompt polishing (template-based)

The primary dataset contains real prompt rewrites by GPT-4 where prompts are
completely restructured with role assignments, formatting, and detail guidance.
Template-based sources supplement with domain-specific coverage.

Usage:
    python -m ai.src.training.collect_sft_data
"""
import csv
import json
import random
import re
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm


# -- Configuration -----------------------------------------------------------

AI_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = AI_DIR.parent
OUTPUT_DIR = AI_DIR / "data" / "sft"
OUTPUT_FILE = OUTPUT_DIR / "prompt_pairs.jsonl"
SAMPLE_FILE = OUTPUT_DIR / "quality_sample_100.jsonl"
SPLITS_DIR = OUTPUT_DIR / "splits"

MATH_CSV = PROJECT_ROOT / "FY_dataset" / "train.csv" / "train.csv"

TARGET_MAX = 25_000
SEED = 42

random.seed(SEED)


# -- Utility: pick a random template ----------------------------------------

def _pick(templates: list[str], **kwargs) -> str:
    return random.choice(templates).format(**kwargs)


# -- MATH dataset pairs ------------------------------------------------------

MATH_TEMPLATES = [
    (
        "{nl_problem}",
        "{action}: $$ {latex_expr} $$\n\n"
        "Show each step using LaTeX notation. Box the final answer as $\\boxed{{result}}$."
    ),
    (
        "{nl_problem}",
        "{action} the following:\n$$ {latex_expr} $$\n\n"
        "Provide a step-by-step solution. Use LaTeX for all mathematical expressions."
    ),
    (
        "{nl_problem}",
        "**Problem ({category}, {level}):**\n$$ {latex_expr} $$\n\n"
        "**Instructions:** Work through each step clearly. "
        "Format all math in LaTeX. Present the final answer as $\\boxed{{answer}}$."
    ),
    (
        "{nl_problem}",
        "{action}:\n$$ {latex_expr} $$\n\n"
        "Requirements:\n"
        "- Show all intermediate steps\n"
        "- Use proper LaTeX notation throughout\n"
        "- Highlight the final answer"
    ),
    (
        "{nl_problem}",
        "**{category} Problem:**\n$$ {latex_expr} $$\n\n"
        "Solve step by step. Express every equation in LaTeX. "
        "Conclude with $\\boxed{{final\\_answer}}$."
    ),
    (
        "{nl_problem}",
        "{action} this {category_lower} problem:\n\n$$ {latex_expr} $$\n\n"
        "Show your reasoning at each step using LaTeX formatting."
    ),
]

def _strip_latex_to_nl(text: str) -> str:
    """Rough conversion of LaTeX-heavy text to natural-language-ish version."""
    nl = text
    nl = re.sub(r'\$\$?([^$]+)\$\$?', r'\1', nl)
    nl = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', nl)
    nl = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', nl)
    nl = re.sub(r'\\boxed\{([^}]+)\}', r'\1', nl)
    nl = re.sub(r'\\text\{([^}]+)\}', r'\1', nl)
    nl = re.sub(r'\\(pi|theta|alpha|beta|gamma|infty)\b', r'\1', nl)
    nl = re.sub(r'\\(sin|cos|tan|log|ln|lim|sum|int)\b', r'\1', nl)
    nl = re.sub(r'\\[a-zA-Z]+', '', nl)
    nl = re.sub(r'[{}]', '', nl)
    nl = re.sub(r'\s+', ' ', nl).strip()
    return nl


def collect_from_math() -> list[dict]:
    """Create prompt-polishing pairs from the local MATH competition dataset."""
    if not MATH_CSV.exists():
        print(f"[WARN] MATH dataset not found at {MATH_CSV}, skipping")
        return []

    print("[MATH] Loading local MATH dataset...")
    pairs = []
    action_words = ["Solve", "Evaluate", "Find", "Compute", "Determine", "Calculate", "Simplify", "Prove"]

    with open(MATH_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in tqdm(rows, desc="   Processing MATH", leave=False):
        problem = row.get("problem", "").strip()
        category = row.get("type", "Math").strip()
        level = row.get("level", "").strip()

        if not problem or len(problem) < 20:
            continue

        latex_expr = problem
        nl_problem = _strip_latex_to_nl(problem)

        if len(nl_problem) < 15 or nl_problem == latex_expr:
            continue

        action = random.choice(action_words)
        template_pair = random.choice(MATH_TEMPLATES)

        bad_prompt = template_pair[0].format(
            nl_problem=nl_problem,
            action=action,
        )
        optimized = template_pair[1].format(
            action=action,
            latex_expr=latex_expr,
            category=category,
            category_lower=category.lower(),
            level=level,
        )

        if len(optimized) > len(bad_prompt) * 1.2:
            pairs.append({"input": bad_prompt, "output": optimized})

    print(f"   [OK] Extracted {len(pairs)} pairs from MATH dataset")
    return pairs


# -- General instruction polishing templates ---------------------------------

GENERAL_TEMPLATES = [
    # Audience-focused
    "Explain {topic} to {audience}.\n\nUse {analogy_style}. Break into {n_sections} sections. "
    "Define technical terms inline. End with a comprehension check question.",

    "Write a clear explanation of {topic} for {audience}.\n\n"
    "Start with a real-world analogy, then progressively add detail across {n_sections} layers.",

    # Structure-focused
    "{instruction}\n\nStructure your response with:\n"
    "1. A one-sentence summary\n"
    "2. Detailed explanation ({word_range} words)\n"
    "3. {n_examples} concrete example(s)\n"
    "4. Key takeaways",

    "{instruction}\n\n"
    "Format: Start with the core answer in bold, then explain your reasoning. "
    "Use bullet points for lists. Keep it under {max_words} words.",

    # Specificity-focused
    "{instruction}\n\n"
    "Be specific: include {detail_type}. "
    "Avoid generic statements. Every claim should have a concrete example.",

    "{instruction}\n\n"
    "Context: {context_hint}\n"
    "Provide an actionable, detailed response with specific recommendations.",

    # Constraint-focused
    "{instruction}\n\n"
    "Constraints: {constraint_1}. {constraint_2}. {constraint_3}.",

    "{instruction}\n\n"
    "Response requirements:\n- {req_1}\n- {req_2}\n- {req_3}",

    # Chain-of-thought
    "{instruction}\n\n"
    "Think through this step by step. Show your reasoning before giving the final answer.",

    "{instruction}\n\n"
    "Break this down into sub-problems. Address each one, then synthesize into a final answer.",

    # Comparison/analysis
    "{instruction}\n\n"
    "Compare at least {n_options} approaches. For each, list pros, cons, and best use case. "
    "Recommend one with justification.",

    "{instruction}\n\n"
    "Analyze from multiple angles: {angle_1}, {angle_2}, and {angle_3}. "
    "Conclude with a balanced recommendation.",
]

AUDIENCES = [
    "a complete beginner", "a 10-year-old", "a college student",
    "a non-technical manager", "someone with no background in the topic",
    "a curious adult with no prior knowledge", "a high school student",
]
ANALOGY_STYLES = [
    "everyday analogies", "a cooking metaphor", "a sports analogy",
    "a building/construction metaphor", "comparisons to familiar objects",
]
DETAIL_TYPES = [
    "numbers, dates, or statistics", "real-world examples",
    "step-by-step instructions", "named tools or resources",
    "before-and-after comparisons", "specific metrics or benchmarks",
]
CONSTRAINTS_POOL = [
    "Keep the response under 200 words",
    "Use simple language (no jargon)",
    "Include at least 2 examples",
    "Use numbered steps",
    "Start with the most important point",
    "End with a practical next step",
    "Cite sources where possible",
    "Use active voice throughout",
    "Avoid filler phrases",
    "Be specific -- no vague generalities",
    "Include a brief summary at the end",
    "Address potential counterarguments",
]
ANGLES = [
    "technical feasibility", "cost", "user experience", "scalability",
    "maintainability", "performance", "security", "simplicity",
    "long-term impact", "short-term benefit", "risk",
]
CONTEXT_HINTS = [
    "This is for a professional setting",
    "The reader has limited time",
    "This will be shared with a team",
    "Accuracy is critical here",
    "This is for a presentation",
    "The audience is skeptical",
]


def _make_general_optimized(instruction: str, context: str = "") -> str:
    """Generate a diverse optimized prompt from a bare instruction."""
    template = random.choice(GENERAL_TEMPLATES)

    topic = instruction[:80].rstrip(".")
    audience = random.choice(AUDIENCES)
    analogy = random.choice(ANALOGY_STYLES)
    n_sec = random.choice(["2", "3", "4"])
    n_ex = random.choice(["1", "2", "3"])
    n_opt = random.choice(["2", "3"])
    word_range = random.choice(["100-200", "200-300", "150-250"])
    max_words = random.choice(["200", "300", "150", "250"])
    detail = random.choice(DETAIL_TYPES)
    constraints = random.sample(CONSTRAINTS_POOL, 3)
    reqs = random.sample(CONSTRAINTS_POOL, 3)
    angles = random.sample(ANGLES, 3)
    ctx = random.choice(CONTEXT_HINTS) if not context else f"Given: {context[:120]}"

    full_instruction = instruction
    if context:
        full_instruction = f"{instruction}\n\nContext: {context}"

    try:
        optimized = template.format(
            instruction=full_instruction,
            topic=topic,
            audience=audience,
            analogy_style=analogy,
            n_sections=n_sec,
            n_examples=n_ex,
            n_options=n_opt,
            word_range=word_range,
            max_words=max_words,
            detail_type=detail,
            context_hint=ctx,
            constraint_1=constraints[0],
            constraint_2=constraints[1],
            constraint_3=constraints[2],
            req_1=reqs[0],
            req_2=reqs[1],
            req_3=reqs[2],
            angle_1=angles[0],
            angle_2=angles[1],
            angle_3=angles[2],
        )
    except (KeyError, IndexError):
        optimized = (
            f"{full_instruction}\n\n"
            f"Be specific and detailed. Include concrete examples. "
            f"Structure your response with clear sections."
        )

    return optimized


# -- Code prompt polishing templates ----------------------------------------

CODE_TEMPLATES = [
    "{instruction}\n\n"
    "Requirements:\n"
    "- Language: {lang}\n"
    "- Include type hints and a docstring\n"
    "- Handle edge cases: {edge_cases}\n"
    "- Add {n_tests} test example(s) with expected output",

    "{instruction}\n\n"
    "Write clean, production-ready {lang} code.\n"
    "Include: error handling, comments on non-obvious logic, "
    "and example usage showing input/output.",

    "{instruction}\n\n"
    "Implement in {lang}. Optimize for {optimize_for}.\n"
    "Show time and space complexity. Include {n_tests} test cases.",

    "{instruction}\n\n"
    "Write a well-structured {lang} solution:\n"
    "1. Function signature with type hints\n"
    "2. Implementation with inline comments\n"
    "3. Edge case handling\n"
    "4. Usage example",

    "{instruction}\n\n"
    "Code requirements:\n"
    "- {lang} with modern best practices\n"
    "- Modular design (separate concerns)\n"
    "- Handle: {edge_cases}\n"
    "- Brief explanation of the approach",
]

LANGUAGES = ["Python", "Python 3", "the appropriate language"]
EDGE_CASES_POOL = [
    "empty input, None values",
    "single element, duplicates",
    "negative numbers, zero",
    "very large input, boundary values",
    "invalid types, missing keys",
    "empty string, whitespace only",
]
OPTIMIZE_FOR = ["readability", "performance", "readability and correctness", "maintainability"]


def _make_code_optimized(instruction: str, input_text: str = "") -> str:
    template = random.choice(CODE_TEMPLATES)
    lang = random.choice(LANGUAGES)
    edge = random.choice(EDGE_CASES_POOL)
    opt = random.choice(OPTIMIZE_FOR)
    n_tests = random.choice(["2", "3"])

    full = instruction
    if input_text:
        full = f"{instruction}\n\nInput:\n```\n{input_text}\n```"

    return template.format(
        instruction=full,
        lang=lang,
        edge_cases=edge,
        optimize_for=opt,
        n_tests=n_tests,
    )


# -- Writing/creative polishing templates -----------------------------------

WRITING_TEMPLATES = [
    "{instruction}\n\n"
    "Length: {length}. Tone: {tone}. "
    "Structure: clear thesis, specific details over generalizations, memorable closing.",

    "{instruction}\n\n"
    "Audience: {audience}. Format: {format_type}.\n"
    "Use vivid language, varied sentence length, and concrete examples.",

    "{instruction}\n\n"
    "Write with a {tone} tone, targeting {audience}.\n"
    "Include: a hook in the opening, {n_points} key points with examples, "
    "and an actionable conclusion.",

    "{instruction}\n\n"
    "Guidelines:\n"
    "- {length}\n"
    "- {tone} tone\n"
    "- Include a compelling opening hook\n"
    "- End with a clear call to action or takeaway",
]

TONES = ["conversational", "professional", "engaging", "authoritative", "friendly", "persuasive"]
LENGTHS = ["150-200 words", "200-300 words", "300-500 words", "Keep it concise (under 250 words)"]
FORMATS = ["blog post", "essay", "article", "short piece", "structured response"]


def _make_writing_optimized(instruction: str) -> str:
    template = random.choice(WRITING_TEMPLATES)
    return template.format(
        instruction=instruction,
        tone=random.choice(TONES),
        audience=random.choice(AUDIENCES),
        length=random.choice(LENGTHS),
        format_type=random.choice(FORMATS),
        n_points=random.choice(["3", "4", "5"]),
    )


# -- Summary/analysis polishing templates -----------------------------------

SUMMARY_TEMPLATES = [
    "{instruction}\n\n"
    "Output format:\n"
    "1. Executive summary (2 sentences)\n"
    "2. Key findings (5-7 bullet points)\n"
    "3. Practical implications",

    "{instruction}\n\n"
    "Provide: a TL;DR (1 sentence), then a structured breakdown with "
    "main points, supporting evidence, and limitations.",

    "{instruction}\n\n"
    "Analyze systematically:\n"
    "- Main argument or finding\n"
    "- Supporting evidence\n"
    "- Counterpoints or limitations\n"
    "- Actionable takeaways",
]


# -- Category detection and routing -----------------------------------------

MATH_KEYWORDS = {
    "math", "algebra", "equation", "solve", "calculate", "compute",
    "derivative", "integral", "polynomial", "factor", "simplif",
    "quadratic", "calculus", "geometry", "trigonometr", "probability",
    "combinat", "theorem", "proof", "prime", "divisib", "matrix",
    "vector", "logarithm", "exponential", "fraction", "ratio",
}
CODE_KEYWORDS = {
    "python", "code", "function", "script", "program", "algorithm",
    "implement", "class", "method", "api", "database", "sql",
    "html", "css", "javascript", "debug", "compile", "binary",
    "array", "list", "sort", "search", "tree", "graph", "hash",
    "regex", "parse", "json", "xml", "http", "server", "cli",
}
WRITING_KEYWORDS = {
    "write", "essay", "article", "story", "creative", "blog",
    "poem", "letter", "email", "speech", "narrative", "describe",
    "compose", "draft", "outline", "paragraph",
    "linkedin", "social media", "post", "tweet", "marketing",
}
SUMMARY_KEYWORDS = {
    "summarize", "summary", "tldr", "key points", "analyze",
    "compare", "contrast", "evaluate", "review", "assess",
    "pros and cons", "advantages", "disadvantages",
}


def _detect_category(text: str) -> str:
    lower = text.lower()
    scores = {
        "math": sum(1 for k in MATH_KEYWORDS if k in lower),
        "code": sum(1 for k in CODE_KEYWORDS if k in lower),
        "writing": sum(1 for k in WRITING_KEYWORDS if k in lower),
        "summary": sum(1 for k in SUMMARY_KEYWORDS if k in lower),
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "general"


# -- Primary data source: real GPT-4 prompt rewrites -------------------------

def collect_from_prompt_preference() -> list[dict]:
    """Load real prompt rewrites from the Prompt Preference Dataset (30K pairs)."""
    print("[HF] Loading Junrulu/Prompt_Preference_Dataset...")
    try:
        ds = load_dataset("Junrulu/Prompt_Preference_Dataset", split="train")
    except Exception as e:
        print(f"   [WARN] Failed: {e}")
        return []

    pairs = []
    for example in tqdm(ds, desc="   Processing PromptPreference", leave=False):
        raw = example.get("raw_prompt", "").strip()
        optimized = example.get("gpt4_optimized_prompt", "").strip()

        if not raw or not optimized:
            continue
        if len(raw) < 8 or len(optimized) < 20:
            continue
        if len(optimized) <= len(raw):
            continue

        pairs.append({"input": raw, "output": optimized})

    print(f"   [OK] Extracted {len(pairs)} pairs from Prompt Preference Dataset")
    return pairs


# -- Template-based data sources ---------------------------------------------

def collect_from_dolly() -> list[dict]:
    print("[HF] Loading databricks/databricks-dolly-15k...")
    try:
        ds = load_dataset("databricks/databricks-dolly-15k", split="train")
    except Exception as e:
        print(f"   [WARN] Failed: {e}")
        return []

    pairs = []
    for example in tqdm(ds, desc="   Processing Dolly", leave=False):
        instruction = example.get("instruction", "").strip()
        context = example.get("context", "").strip()
        if not instruction or len(instruction) < 10:
            continue

        bad_prompt = instruction
        cat = _detect_category(instruction)

        if cat == "code":
            optimized = _make_code_optimized(instruction)
        elif cat == "writing":
            optimized = _make_writing_optimized(instruction)
        elif cat == "summary":
            optimized = random.choice(SUMMARY_TEMPLATES).format(instruction=instruction)
        else:
            optimized = _make_general_optimized(instruction, context)

        if len(optimized) > len(bad_prompt) * 1.2:
            pairs.append({"input": bad_prompt, "output": optimized})

    print(f"   [OK] Extracted {len(pairs)} pairs from Dolly")
    return pairs


def collect_from_alpaca() -> list[dict]:
    print("[HF] Loading tatsu-lab/alpaca...")
    try:
        ds = load_dataset("tatsu-lab/alpaca", split="train")
    except Exception as e:
        print(f"   [WARN] Failed: {e}")
        return []

    pairs = []
    for example in tqdm(ds, desc="   Processing Alpaca", leave=False):
        instruction = example.get("instruction", "").strip()
        input_text = example.get("input", "").strip()
        if not instruction or len(instruction) < 10:
            continue

        bad_prompt = instruction
        cat = _detect_category(instruction)

        if cat == "code":
            optimized = _make_code_optimized(instruction, input_text)
        elif cat == "writing":
            optimized = _make_writing_optimized(instruction)
        elif cat == "summary":
            optimized = random.choice(SUMMARY_TEMPLATES).format(
                instruction=instruction if not input_text else f"{instruction}\n\nText: {input_text}"
            )
        else:
            optimized = _make_general_optimized(instruction, input_text)

        if len(optimized) > len(bad_prompt) * 1.2:
            pairs.append({"input": bad_prompt, "output": optimized})

    print(f"   [OK] Extracted {len(pairs)} pairs from Alpaca")
    return pairs


def collect_from_code_alpaca() -> list[dict]:
    print("[HF] Loading sahil2801/CodeAlpaca-20k...")
    try:
        ds = load_dataset("sahil2801/CodeAlpaca-20k", split="train")
    except Exception as e:
        print(f"   [WARN] Failed: {e}")
        return []

    pairs = []
    for example in tqdm(ds, desc="   Processing CodeAlpaca", leave=False):
        instruction = example.get("instruction", "").strip()
        input_text = example.get("input", "").strip()
        if not instruction or len(instruction) < 10:
            continue

        bad_prompt = instruction
        optimized = _make_code_optimized(instruction, input_text)

        if len(optimized) > len(bad_prompt) * 1.2:
            pairs.append({"input": bad_prompt, "output": optimized})

    print(f"   [OK] Extracted {len(pairs)} pairs from CodeAlpaca")
    return pairs


# -- Main pipeline -----------------------------------------------------------

def collect_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("[SFT] Prompt Polisher -- SFT Data Collection (v3 - real rewrites)")
    print("=" * 70)

    all_pairs = []

    # 1. PRIMARY: Real GPT-4 prompt rewrites (highest quality)
    all_pairs.extend(collect_from_prompt_preference())

    # 2. MATH dataset (local) -- LaTeX optimization
    all_pairs.extend(collect_from_math())

    # 3. Supplementary template-based sources
    all_pairs.extend(collect_from_dolly())
    all_pairs.extend(collect_from_code_alpaca())

    print(f"\n[STATS] Total collected: {len(all_pairs)} pairs")

    # Deduplicate by input
    seen = set()
    unique = []
    for pair in all_pairs:
        key = pair["input"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(pair)

    print(f"[STATS] After dedup: {len(unique)} unique pairs")

    random.shuffle(unique)

    if len(unique) > TARGET_MAX:
        unique = unique[:TARGET_MAX]
        print(f"[STATS] Capped at: {len(unique)} pairs")

    # Save full dataset
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for pair in unique:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"\n[FILE] Saved: {OUTPUT_FILE} ({len(unique)} pairs)")

    # Quality sample
    sample = random.sample(unique, min(100, len(unique)))
    with open(SAMPLE_FILE, "w", encoding="utf-8") as f:
        for pair in sample:
            f.write(json.dumps(pair, ensure_ascii=False, indent=2) + "\n\n")
    print(f"[FILE] Quality sample: {SAMPLE_FILE} ({len(sample)} pairs)")

    # Train/val/test splits
    print(f"\n[SPLIT] Creating data splits...")
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    n = len(unique)
    n_train = int(n * 0.9)
    n_val = int(n * 0.05)

    splits = {
        "train": unique[:n_train],
        "val": unique[n_train:n_train + n_val],
        "test": unique[n_train + n_val:],
    }

    for name, data in splits.items():
        path = SPLITS_DIR / f"{name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for pair in data:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        print(f"   {name}: {len(data)} examples")

    print("\n" + "=" * 70)
    print("[DONE] SFT data collection complete!")
    print("=" * 70)


if __name__ == "__main__":
    collect_all()
