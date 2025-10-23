# Prompting, Debugging, and Innovation for Code Generation using LLMs

**Author:** Suyash Maniyar
**Course:** CSE 520 — Assignment 1
**Repository:** [LLM_code_generation_520_exercise1](https://github.com/SuyashManiyar/LLM_code_generation_520_exercise1)

---

## Overview

This project explores prompt engineering, automated debugging, and iterative reasoning in code generation using Large Language Models (LLMs).
It evaluates and compares multiple prompting strategies on the HumanEval dataset, builds an automated evaluation pipeline, and proposes a hybrid small–large LLM collaboration system to improve code correctness efficiently.

---

## Objectives

1. Investigate the effectiveness of **Self-Planning** and **Self-Editing** prompting techniques.
2. Evaluate code generation performance on the **HumanEval** benchmark.
3. Develop a debugging pipeline that automatically detects and resolves code errors.
4. Propose a **multi-model reasoning pipeline** combining smaller, cost-efficient LLMs with larger reasoning models (e.g., GPT-4, Gemini 2.5 Pro).

---

## Models Used

| Type                      | Model                |
| ------------------------- | -------------------- |
| Small LLM                 | gemma-3-27b-it       |
| Small LLM                 | llama-3.1-8b-instant |
| Large LLM (for reasoning) | GPT-4                |
| Large LLM (for reasoning) | Gemini 2.5 Pro       |

---

## Dataset

* **HumanEval Dataset**
  Benchmark for evaluating LLM-based code generation and correctness using functional test cases.
  Used for pass@1 and pass@3 evaluation.

---

## Prompting Techniques

### 1. Self-Planning Prompting

**Structure:**

```
You are an expert Python programmer. Given the question, develop Python code that directly runs.
Before starting the code, write reasoning in Python comments explaining your plan.

{Problem Statement}
```

**Key Idea:**
The model first reasons about the solution in comments before coding, improving logical flow and clarity.

**Results:**

| Model                | Pass@1 | Pass@3 |
| -------------------- | ------ | ------ |
| gemma-3-27b-it       | 80%    | 80%    |
| llama-3.1-8b-instant | 70%    | 80%    |

---

### 2. Self-Editing Prompting

**Structure:**

```json
{
  "code_attempt_1": "<first version of python code with inline comments>",
  "reflection_on_why_this_code_might_fail": "<short reflection on why the first code might fail or edge cases it might miss>",
  "code_attempt_2": "<improved python code with inline comments>"
}
```

**Key Idea:**
The model generates code, reflects on potential errors or missed cases, and then regenerates an improved version.

**Results:**

| Model                | Pass@1 | Pass@3 |
| -------------------- | ------ | ------ |
| gemma-3-27b-it       | 80%    | 90%    |
| llama-3.1-8b-instant | 80%    | 80%    |

---

## Debugging and Iterative Improvement

When models failed on certain tasks (e.g., `iscube()` or `solve(N)`), the pipeline used **reasoning augmentation** with larger LLMs (GPT-4 or Gemini).

### Process

1. Identify failure using automated test evaluation.
2. Generate structured reasoning steps using GPT-4.
3. Feed improved reasoning back into the small model (Gemma or Llama).
4. Regenerate and re-evaluate the corrected code.

This reasoning-assisted loop successfully resolved all previously failing cases.

---

## Innovation: Multi-LLM Collaborative Pipeline

### Workflow

1. **Problem Definition:** Read and parse the task.
2. **Prompt Creation:** Generate a structured prompt.
3. **Initial Solution Generation:** Small LLM produces first draft.
4. **Evaluation:** Automatically test the output.
5. **Iterative Self-Correction:** Small LLM self-corrects up to three times.
6. **Escalation:** If failures persist, large LLM (GPT-4 or Gemini) analyzes reasoning errors.
7. **Re-generation:** Small LLM regenerates code based on large model’s reasoning.
8. **Re-evaluation:** Code is tested again for correctness.
9. **Completion:** The system stops after success or maximum iterations.

### Results

| Dataset                 | Small LLM            | Large LLM      | Pass@1 | Pass@3 |
| ----------------------- | -------------------- | -------------- | ------ | ------ |
| HumanEval (10 problems) | gemma-3-27b-it       | GPT-4          | 100%   | 100%   |
| HumanEval (10 problems) | llama-3.1-8b-instant | GPT-4          | 100%   | 100%   |
| HumanEval (10 problems) | gemma-3-27b-it       | Gemini 2.5 Pro | 100%   | 100%   |
| HumanEval (10 problems) | llama-3.1-8b-instant | Gemini 2.5 Pro | 100%   | 100%   |

---

## Key Insights

* **Self-Edit prompting** outperforms **Self-Planning** by leveraging model reflection.
* **Reasoning augmentation** from larger models bridges logic gaps in smaller ones.
* **Multi-LLM pipelines** combine reasoning depth with generation efficiency.
* Using large LLMs selectively reduces computational cost while improving accuracy.

---

## Future Work

* Automate model selection based on task complexity.
* Integrate reinforcement learning for adaptive prompt optimization.
* Extend the system for multilingual code generation and generalized error pattern analysis.

---

## License

This project is open-sourced under the MIT License.

---



