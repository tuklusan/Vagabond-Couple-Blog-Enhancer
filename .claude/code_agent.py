import os
import sys
import re
import argparse
import time
from pathlib import Path

import requests


def load_key(var_name, filepath, prefix):
    """Load API key from environment variable or config file."""
    key = os.environ.get(var_name)
    if key:
        return key.strip()

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(prefix + '='):
                    return line[len(prefix)+1:].strip()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        sys.exit(1)

    print(f"Error: {prefix} not found in {filepath} or environment variable {var_name}")
    sys.exit(1)


def safe_print(message):
    """Print with ASCII-safe encoding."""
    print(str(message).encode('ascii', 'replace').decode('ascii'))


def call_deepseek(messages, api_key, model="deepseek-v4-pro", max_retries=2):
    """Call DeepSeek API with retry logic for 503/timeout."""
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 8192
    }

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 503:
                safe_print(f"DeepSeek 503 error, attempt {attempt+1}/{max_retries+1}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            safe_print(f"DeepSeek timeout, attempt {attempt+1}/{max_retries+1}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise
        except requests.exceptions.RequestException as e:
            safe_print(f"DeepSeek API error: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise


def call_nvidia(messages, api_key, model="nvidia/nemotron-3-super-120b-a12b"):
    """Call NVIDIA NIM API with configurable model."""
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 8192
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        safe_print(f"NVIDIA API error ({model}): {e}")
        raise


def strip_markdown_fences(text):
    """Remove markdown code fences from response."""
    pattern = r'```(?:python)?\s*\n?(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def write_code(task, context="", previous_code="", review_feedback="",
               deepseek_key="", nvidia_key=""):
    """Generate code using primary (DeepSeek) or fallback (Mistral via NVIDIA) model."""

    system_prompt = (
        "You are an expert Python developer. Return ONLY raw Python code. "
        "No markdown fences, no explanation, no backticks. "
        "Just the code itself."
    )

    user_parts = [f"Task: {task}"]
    if context:
        user_parts.append(f"Context: {context}")
    if previous_code:
        user_parts.append(f"Previous code:\n{previous_code}")
    if review_feedback:
        user_parts.append(f"Review feedback to address:\n{review_feedback}")

    user_prompt = "\n\n".join(user_parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Try primary (DeepSeek)
    try:
        safe_print("Calling DeepSeek (primary coder)...")
        response = call_deepseek(messages, deepseek_key)
        code = strip_markdown_fences(response)
        return code, "deepseek-v4-pro"
    except Exception as e:
        safe_print(f"Primary coder failed: {e}")
        safe_print("Switching to fallback (Mistral via NVIDIA)...")

    # Try fallback (Mistral via NVIDIA)
    try:
        safe_print("Calling Mistral (fallback coder)...")
        response = call_nvidia(messages, nvidia_key)
        code = strip_markdown_fences(response)
        return code, "mistral-large"
    except Exception as e:
        safe_print(f"Fallback coder failed: {e}")
        sys.exit(1)


def review_code(code, task, deepseek_key="", nvidia_key=""):
    """Review code using DeepSeek (primary) or Qwen via NVIDIA (fallback)."""

    system_prompt = (
        "You are a Python code reviewer. Review the code for correctness, bugs, "
        "security issues, edge cases, and style. "
        "Group your findings as Critical/Warning/Info. "
        "If there are NO Critical issues, you MUST end your response with exactly: APPROVED"
    )

    user_prompt = f"Task: {task}\n\nCode to review:\n{code}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    review = None
    primary_error = None

    # Try primary reviewer (DeepSeek)
    try:
        safe_print("Calling DeepSeek (primary code reviewer)...")
        review = call_deepseek(messages, deepseek_key)
    except Exception as e:
        primary_error = e
        safe_print(f"Primary reviewer failed: {e}")

    # Try fallback reviewer (Qwen via NVIDIA)
    if review is None:
        try:
            safe_print("Calling Qwen (fallback code reviewer)...")
            review = call_nvidia(messages, nvidia_key,
                                 model="qwen/qwen3-coder-480b-a35b-instruct")
        except Exception as e2:
            safe_print(f"Fallback reviewer failed: {e2}")
            return True, f"Review failed: primary={primary_error}, fallback={e2}"

    # Check for approval
    approved = bool(re.search(r'(?<!\bNOT\s)\bAPPROVED\b', review, re.IGNORECASE))
    has_critical = bool(re.search(r'\bcritical\b', review, re.IGNORECASE))

    if approved:
        has_critical = False

    return has_critical, review


def main():
    parser = argparse.ArgumentParser(description="AI Code Agent")
    parser.add_argument("--task", required=True, help="Coding task description")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--context", default="", help="Additional context")
    args = parser.parse_args()

    # Load API keys
    deepseek_key = load_key(
        "DEEPSEEK_API_KEY",
        "Config/_SECRETS/deepseek-api-key.txt",
        "DEEPSEEK_API_KEY"
    )
    nvidia_key = load_key(
        "NVIDIA_API_KEY_CODING",
        "Config/_SECRETS/nvidia-api-keys.txt",
        "NVIDIA_API_KEY_CODING"
    )

    safe_print(f"Task: {args.task}")
    safe_print(f"Output: {args.output}")

    previous_code = ""
    review_feedback = ""
    final_code = ""
    final_review = ""

    for round_num in range(1, 4):
        safe_print(f"\n{'='*60}")
        safe_print(f"Round {round_num}/3")
        safe_print(f"{'='*60}")

        # Write code
        code, coder_name = write_code(
            task=args.task,
            context=args.context,
            previous_code=previous_code,
            review_feedback=review_feedback,
            deepseek_key=deepseek_key,
            nvidia_key=nvidia_key
        )
        safe_print(f"Coder used: {coder_name}")
        safe_print(f"Code length: {len(code)} chars")

        # Review code
        has_critical, review = review_code(
            code=code,
            task=args.task,
            deepseek_key=deepseek_key,
            nvidia_key=nvidia_key
        )
        safe_print(f"Review has critical issues: {has_critical}")
        safe_print(f"Review:\n{review}")

        previous_code = code
        review_feedback = review
        final_code = code
        final_review = review

        if not has_critical:
            safe_print("Code APPROVED!")
            break

        if round_num < 3:
            safe_print("Code needs improvement, retrying...")

    # Write output files
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_code)
    safe_print(f"Code written to: {output_path}")

    review_path = output_path.with_suffix(output_path.suffix + ".review.txt")
    with open(review_path, 'w', encoding='utf-8') as f:
        f.write(final_review)
    safe_print(f"Review written to: {review_path}")


if __name__ == "__main__":
    main()
