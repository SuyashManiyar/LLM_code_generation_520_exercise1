import os
import re
import json
import pandas as pd
from pathlib import Path
from human_eval.execution import check_correctness
from human_eval.data import read_problems
from groq import Groq

# =======================
# MODEL SETUP
# =======================
MODEL_NAME = "llama-3.3-70b-versatile"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def groq_generate(prompt: str, model_name: str = MODEL_NAME, temperature: float = 0.7, max_tokens: int = 2048):
    """Generate text using Groq ChatCompletion API."""
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful Python assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()

# =======================
# LOAD HUMAN EVAL PROBLEMS
# =======================
problems = read_problems()
my_list = [
    "HumanEval/1",  # Add more IDs here
]
selected_problems = {k: problems[k] for k in problems if k in my_list}

# =======================
# PROMPTS
# =======================
prefix_prompt = '''You are an expert Python programmer. For the given problem, provide output in the following structured format:
{
"code_attempt_1" : "<first version of python code with inline comments>",
"reflection_on_why_this_code_might_fail" : "<short reflection on why the first code might fail or edge cases it might miss and corrections to make so that it does not miss those cases>",
"code_attempt_2" : "<improved python code with inline comments>"
}
'''

suffix_prompt = "\nOnly return the output in this JSON-like structure. Do not add extra explanations outside of this structure."

# =======================
# ROBUST EXTRACTION FUNCTION
# =======================
def extract_json_fields(text):
    """Extract structured code/reflection fields from model output safely."""
    cleaned = re.sub(r"^```[a-zA-Z]*|```$", "", text.strip(), flags=re.MULTILINE).strip()

    # Try proper JSON parsing first
    try:
        parsed = json.loads(cleaned)
        return {
            "code_attempt_1": parsed.get("code_attempt_1", "").strip(),
            "reflection": parsed.get("reflection_on_why_this_code_might_fail", "").strip(),
            "code_attempt_2": parsed.get("code_attempt_2", "").strip(),
        }
    except json.JSONDecodeError:
        pass  # fallback to regex

    def extract_field_fallback(field_name):
        pattern = rf'"{field_name}"\s*:\s*"([\s\S]*?)"(?=\s*,\s*"[a-z_]+":|\s*\}})'
        match = re.search(pattern, cleaned)
        if match:
            return match.group(1).replace('\\"', '"').strip()
        return ""

    return {
        "code_attempt_1": extract_field_fallback("code_attempt_1"),
        "reflection": extract_field_fallback("reflection_on_why_this_code_might_fail"),
        "code_attempt_2": extract_field_fallback("code_attempt_2"),
    }

# =======================
# GENERATE MULTIPLE ATTEMPTS
# =======================
def generate_attempts(problem_prompt, num_samples=3):
    """Generate multiple code_attempt_2 samples for stochastic evaluation."""
    attempts = []
    for i in range(num_samples):
        print(f"Generating independent attempt {i+1}/{num_samples}...")
        full_prompt = prefix_prompt + problem_prompt + suffix_prompt
        text = groq_generate(full_prompt, temperature=1.0)
        fields = extract_json_fields(text)
        attempts.append(fields["code_attempt_2"])
    return attempts

# =======================
# MAIN PIPELINE
# =======================
output_dir = Path("groq_model_outputs")
output_dir.mkdir(exist_ok=True)
csv_path = Path("humaneval_full_pipeline_groq.csv")

# Create CSV headers if not present
if not csv_path.exists():
    pd.DataFrame(columns=[
        "problem_id", "full_prompt", "prompt",
        "code_attempt_1", "reflection", "code_attempt_2",
        "eval_attempt_1", "eval_attempt_2", "eval_attempt_3",
        "pass@1_code_attempt_1", "pass@1_code_attempt_2",
        "pass@1_eval", "pass@3_eval"
    ]).to_csv(csv_path, index=False)

# Load already processed problems (for resume capability)
if csv_path.exists():
    processed_ids = set(pd.read_csv(csv_path)["problem_id"])
else:
    processed_ids = set()

for idx, (key, problem) in enumerate(selected_problems.items(), start=1):
    if key in processed_ids:
        print(f"⏩ Skipping {key} (already processed).")
        continue

    print(f"\n=== Processing problem {idx}/{len(selected_problems)}: {key} ===")

    full_prompt = prefix_prompt + problem['prompt'] + suffix_prompt

    print("Generating main structured output...")
    text = groq_generate(full_prompt, temperature=1.0)

    # Save raw model output
    raw_path = output_dir / f"{key.replace('/', '_')}_raw.txt"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Extract fields
    fields = extract_json_fields(text)
    code_attempt_1 = fields["code_attempt_1"]
    reflection = fields["reflection"]
    code_attempt_2 = fields["code_attempt_2"]

    # Evaluate correctness for main attempts
    print("Checking correctness for code_attempt_1 and code_attempt_2...")
    correctness_attempt1 = check_correctness(problem, code_attempt_1, timeout=10.0)
    correctness_attempt2 = check_correctness(problem, code_attempt_2, timeout=10.0)
    pass1_attempt1 = 1 if correctness_attempt1 else 0
    pass1_attempt2 = 1 if correctness_attempt2 else 0

    # Generate additional samples for Pass@K
    print("Generating 3 independent samples for Pass@K evaluation...")
    code_attempts_for_eval = generate_attempts(problem['prompt'], num_samples=3)
    correctness_eval = [check_correctness(problem, code, timeout=10.0) for code in code_attempts_for_eval]
    pass1_eval = 1 if correctness_eval[0] else 0
    pass3_eval = 1 if any(correctness_eval) else 0

    # Build record
    result = {
        "problem_id": key,
        "full_prompt": full_prompt,
        "prompt": problem['prompt'],
        "code_attempt_1": code_attempt_1,
        "reflection": reflection,
        "code_attempt_2": code_attempt_2,
        "eval_attempt_1": code_attempts_for_eval[0],
        "eval_attempt_2": code_attempts_for_eval[1],
        "eval_attempt_3": code_attempts_for_eval[2],
        "pass@1_code_attempt_1": pass1_attempt1,
        "pass@1_code_attempt_2": pass1_attempt2,
        "pass@1_eval": pass1_eval,
        "pass@3_eval": pass3_eval,
    }

    # Save individual JSON
    with open(output_dir / f"{key.replace('/', '_')}_parsed.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Incrementally append to CSV
    pd.DataFrame([result]).to_csv(csv_path, mode='a', index=False, header=False)

    print(f"✅ Completed {key}: "
          f"Attempt1={pass1_attempt1}, Attempt2={pass1_attempt2}, "
          f"EvalPass@1={pass1_eval}, EvalPass@3={pass3_eval}")
    print(f"📄 Appended results to {csv_path}")

print("\n🎯 All problems completed.")
print(f"📁 Master CSV: {csv_path.resolve()}")
print(f"📂 Outputs saved to: {output_dir.resolve()}")
