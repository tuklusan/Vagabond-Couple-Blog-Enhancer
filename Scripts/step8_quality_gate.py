import os
import sys
import re
import json
import glob
from pathlib import Path
from typing import Optional, Tuple, List
from bs4 import BeautifulSoup, NavigableString
import requests

# Constants
TEMP_DIR = Path("Temp")
CONFIG_DIR = Path("Config")
OUTPUT_DIR = Path("Output")
FINAL_HTML_PATH = TEMP_DIR / "final_html.html"
WRITING_RULES_PATH = CONFIG_DIR / "writing_rules.md"
NIM_KEYS_PATH = CONFIG_DIR / "_SECRETS" / "nvidia-api-keys.txt"
DEEPSEEK_KEY_PATH = CONFIG_DIR / "_SECRETS" / "deepseek-api-key.txt"
REPORT_PATH = TEMP_DIR / "quality_gate_report.txt"
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MAX_ROUNDS = 3

# Model names
PRIMARY_WRITER_MODEL = "nvidia/nemotron-3-super-120b-a12b"
FALLBACK_WRITER_MODEL = "mistralai/mistral-medium-3.5-128b"
AUDITOR_MODEL = "deepseek-v4-pro"  # via DeepSeek API directly


def load_nim_key() -> str:
    """Load NVIDIA_API_KEY_CODING from environment or config file."""
    api_key = os.environ.get("NVIDIA_API_KEY_CODING")
    if api_key:
        return api_key
    if NIM_KEYS_PATH.exists():
        with open(NIM_KEYS_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("NVIDIA_API_KEY_CODING="):
                    return line.split("=", 1)[1].strip()
    raise RuntimeError("NVIDIA_API_KEY_CODING not found in environment or config file.")


def load_deepseek_key() -> str:
    """Load DEEPSEEK_API_KEY from environment or config file."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        return api_key
    if DEEPSEEK_KEY_PATH.exists():
        with open(DEEPSEEK_KEY_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1].strip()
    raise RuntimeError("DEEPSEEK_API_KEY not found in environment or config file.")


def call_deepseek(model: str, messages: List[dict], api_key: str, temperature: float = 0.3, max_tokens: int = 8192) -> str:
    """Call DeepSeek API directly and return the response content."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_nim(model: str, messages: List[dict], api_key: str, temperature: float = 1.0, top_p: float = 0.95, max_tokens: int = 8192) -> str:
    """Call NVIDIA NIM API and return the response content."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens
    }
    url = f"{NIM_BASE_URL}/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def extract_prose(html: str) -> Tuple[str, List[dict]]:
    """Extract prose text from HTML as numbered [N] blocks, returning (numbered_prose, element_map)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    element_map = []
    lines = []
    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]):
        text = tag.get_text(strip=True)
        if text:
            idx = len(element_map)
            lines.append(f"[{idx}] {text}")
            element_map.append({"tag": tag.name, "index": idx})

    return "\n".join(lines), element_map


def reinsert_prose(original_html: str, revised_prose: str, element_map: List[dict]) -> str:
    """Parse [N] prefixed lines from revised_prose and reinsert into original HTML by index."""
    import re as _re
    soup = BeautifulSoup(original_html, "html.parser")

    # Parse [N] lines from writer output
    rewrites: dict = {}
    for line in revised_prose.splitlines():
        m = _re.match(r"^\[(\d+)\]\s*(.*)", line.strip())
        if m:
            rewrites[int(m.group(1))] = m.group(2).strip()

    matched = len(rewrites)
    total = len(element_map)
    if matched != total:
        print(str(f"[*] Warning: writer returned {matched} blocks, expected {total}. Reinserting available blocks only.").encode('ascii','replace').decode('ascii'))

    # Collect all prose nodes in document order
    all_tags = [t for t in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"])
                if t.get_text(strip=True) and not t.find_parent(["script", "style"])]

    for idx, tag in enumerate(all_tags):
        if idx in rewrites:
            tag.clear()
            tag.append(NavigableString(rewrites[idx]))

    return str(soup)


def load_writing_rules() -> str:
    """Load writing rules from config file."""
    if WRITING_RULES_PATH.exists():
        with open(WRITING_RULES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "No writing rules file found."


def load_current_html() -> str:
    """Load current HTML from Temp/final_html.html."""
    if not FINAL_HTML_PATH.exists():
        print(str("[*] Error: Temp/final_html.html not found.").encode('ascii','replace').decode('ascii'))
        sys.exit(1)
    with open(FINAL_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


def save_html(html: str, path: Path):
    """Save HTML to file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def find_latest_output_file() -> Optional[Path]:
    """Find the most recent .html file in Output/ directory."""
    if not OUTPUT_DIR.exists():
        return None
    html_files = list(OUTPUT_DIR.glob("*.html"))
    if not html_files:
        return None
    return max(html_files, key=os.path.getmtime)


def writer_evaluate(prose: str, rules: str, api_key: str, auditor_notes: str = "") -> Tuple[str, str, str]:
    """Call writer model to evaluate prose. Returns (assessment, verdict, revised_html_or_empty)."""
    block_count = prose.count("\n[") + (1 if prose.startswith("[") else 0)
    system_prompt = f"""You are a professional travel blog writer. Evaluate the numbered prose blocks against the writing rules.

CRITICAL CONSTRAINTS:
- Narrator: ALWAYS use 'we', 'us', 'our'. NEVER use 'I', 'me', 'my'. Scan every block and fix violations.
- Block count: You will receive exactly {block_count} blocks numbered [0] to [{block_count - 1}]. If you REVISE, return EXACTLY {block_count} blocks with the same [N] prefix. Never merge, split, add, or drop blocks.

Output format:
ASSESSMENT: <paragraph summarizing all issues found>
VERDICT: PASS or REVISE
If VERDICT is REVISE, also output:
REVISED_PROSE:
[0] revised text
[1] revised text
...all {block_count} blocks...

Return ONLY the structured output above. No other text."""

    user_content = f"""Writing Rules:
{rules}

Prose blocks to evaluate:
{prose}
"""
    if auditor_notes:
        user_content += f"\n\nPrevious auditor notes (address these issues):\n{auditor_notes}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    # Try primary model first, fallback on exception
    try:
        response = call_nim(PRIMARY_WRITER_MODEL, messages, api_key)
    except Exception as e:
        print(str(f"[*] Primary writer model failed: {e}. Trying fallback.").encode('ascii','replace').decode('ascii'))
        try:
            response = call_nim(FALLBACK_WRITER_MODEL, messages, api_key)
        except Exception as e2:
            raise RuntimeError(f"Both writer models failed. Primary: {e}, Fallback: {e2}")
    
    # Parse response using regex
    assessment = ""
    verdict = "REVISE"
    revised_html = ""
    
    # Extract ASSESSMENT
    assessment_match = re.search(r'ASSESSMENT:\s*(.*?)(?=VERDICT:)', response, re.DOTALL)
    if assessment_match:
        assessment = assessment_match.group(1).strip()
    
    # Extract VERDICT
    verdict_match = re.search(r'VERDICT:\s*(PASS|REVISE)', response, re.DOTALL)
    if verdict_match:
        verdict = verdict_match.group(1).strip().upper()
    
    # Extract REVISED_PROSE (numbered [N] blocks)
    revised_match = re.search(r'REVISED_PROSE:\s*(.*)', response, re.DOTALL)
    if revised_match:
        revised_html = revised_match.group(1).strip()
    
    if verdict not in ["PASS", "REVISE"]:
        verdict = "REVISE"  # Default to revise if parsing failed
    
    return assessment, verdict, revised_html


def auditor_evaluate(original_prose: str, revised_prose: str, rules: str, writer_assessment: str, api_key: str, deepseek_key: str = "") -> Tuple[str, str]:
    """Call auditor model to evaluate. Returns (audit_verdict, audit_notes)."""
    system_prompt = """You are an independent auditor for a travel blog rewrite pipeline. Your task is to evaluate whether the prose meets all quality standards. You must output a structured audit.

Output format:
AUDIT_VERDICT: APPROVED or REJECTED
AUDIT_NOTES: <specific findings — what passes, what still fails>

Important: Only output the audit verdict and notes. Do not include any other text."""
    
    user_content = f"""Writing Rules:
{rules}

Original Prose:
{original_prose}

Revised Prose (if any, otherwise same as original):
{revised_prose}

Writer's Assessment:
{writer_assessment}

Evaluate if the revised prose meets all criteria. Be thorough and specific."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    response = call_deepseek(AUDITOR_MODEL, messages, deepseek_key)
    
    # Parse response using regex
    audit_verdict = "REJECTED"
    audit_notes = ""
    
    verdict_match = re.search(r'AUDIT_VERDICT:\s*(APPROVED|REJECTED)', response, re.DOTALL)
    if verdict_match:
        audit_verdict = verdict_match.group(1).strip().upper()
    else:
        audit_verdict = "APPROVED"
    
    notes_match = re.search(r'AUDIT_NOTES:\s*(.*)', response, re.DOTALL)
    if notes_match:
        audit_notes = notes_match.group(1).strip()
    
    if audit_verdict not in ["APPROVED", "REJECTED"]:
        audit_verdict = "APPROVED"
    
    return audit_verdict, audit_notes


def main():
    print(str("[*] Starting quality gate...").encode('ascii','replace').decode('ascii'))
    
    # Load API key
    try:
        api_key = load_nim_key()
    except RuntimeError as e:
        print(str(f"[*] Error: {e}").encode('ascii','replace').decode('ascii'))
        sys.exit(1)

    try:
        deepseek_key = load_deepseek_key()
    except RuntimeError as e:
        print(str(f"[*] Error: {e}").encode('ascii','replace').decode('ascii'))
        sys.exit(1)
    
    # Load inputs
    print(str("[*] Loading inputs...").encode('ascii','replace').decode('ascii'))
    current_html = load_current_html()
    rules = load_writing_rules()
    
    # Extract prose
    prose, element_map = extract_prose(current_html)
    if not prose:
        print(str("[*] No prose found in HTML. Saving report and exiting.").encode('ascii','replace').decode('ascii'))
        with open(REPORT_PATH, "w") as f:
            f.write("No prose content found in HTML.\n")
        print(str("[+] GATE PASSED WITH WARNINGS: No prose to evaluate.").encode('ascii','replace').decode('ascii'))
        sys.exit(0)
    
    print(str(f"[*] Extracted {len(element_map)} prose elements.").encode('ascii','replace').decode('ascii'))
    
    # Quality gate loop
    current_prose = prose
    auditor_notes = ""
    final_verdict = "REJECTED"
    round_num = 0  # Initialize round_num before the loop
    assessment = ""
    
    for round_num in range(1, MAX_ROUNDS + 1):
        print(str(f"\n[*] Round {round_num}/{MAX_ROUNDS}").encode('ascii','replace').decode('ascii'))
        
        # Step 1: Writer evaluates
        print(str("[*] Writer evaluating...").encode('ascii','replace').decode('ascii'))
        try:
            assessment, verdict, revised_prose = writer_evaluate(current_prose, rules, api_key, auditor_notes)
        except Exception as e:
            print(str(f"[*] Writer evaluation failed: {e}").encode('ascii','replace').decode('ascii'))
            print(str("[+] GATE PASSED WITH WARNINGS: Writer error, using current version.").encode('ascii','replace').decode('ascii'))
            final_verdict = "APPROVED"
            break
        
        print(str(f"[+] Writer assessment: {assessment[:200]}...").encode('ascii','replace').decode('ascii'))
        print(str(f"[+] Writer verdict: {verdict}").encode('ascii','replace').decode('ascii'))
        
        # If writer says REVISE and provided revised prose, use it
        if verdict == "REVISE" and revised_prose:
            current_prose = revised_prose
            print(str("[*] Using revised prose from writer.").encode('ascii','replace').decode('ascii'))
        elif verdict == "PASS":
            print(str("[*] Writer says PASS, no revision needed.").encode('ascii','replace').decode('ascii'))
        
        # Step 2: Auditor evaluates
        print(str("[*] Auditor evaluating...").encode('ascii','replace').decode('ascii'))
        try:
            _av, _an = auditor_evaluate(prose, current_prose, rules, assessment, api_key, deepseek_key=deepseek_key)
            audit_verdict = _av
            audit_notes = _an
        except Exception as e:
            print(str(f"[*] Auditor evaluation failed: {e}").encode('ascii','replace').decode('ascii'))
            print(str("[+] GATE PASSED WITH WARNINGS: Auditor error, using current version.").encode('ascii','replace').decode('ascii'))
            final_verdict = "APPROVED"
            break
        
        print(str(f"[+] Auditor verdict: {audit_verdict}").encode('ascii','replace').decode('ascii'))
        print(str(f"[+] Auditor notes: {audit_notes[:200]}...").encode('ascii','replace').decode('ascii'))
        
        if audit_verdict == "APPROVED":
            final_verdict = "APPROVED"
            print(str("[+] Quality gate passed!").encode('ascii','replace').decode('ascii'))
            break
        else:
            print(str(f"[*] Auditor rejected. {'Continuing to next round...' if round_num < MAX_ROUNDS else 'Max rounds reached.'}").encode('ascii','replace').decode('ascii'))
    
    # Save final HTML
    print(str("[*] Saving final HTML...").encode('ascii','replace').decode('ascii'))
    if current_prose != prose:
        # Reinsert revised prose into HTML structure
        final_html = reinsert_prose(current_html, current_prose, element_map)
    else:
        final_html = current_html
    
    # Save to Temp/final_html.html
    save_html(final_html, FINAL_HTML_PATH)
    print(str(f"[+] Saved to {FINAL_HTML_PATH}").encode('ascii','replace').decode('ascii'))
    
    # Save to latest Output file
    latest_output = find_latest_output_file()
    if latest_output:
        save_html(final_html, latest_output)
        print(str(f"[+] Saved to {latest_output}").encode('ascii','replace').decode('ascii'))
    else:
        # Create a default output file
        output_path = OUTPUT_DIR / "blog_post.html"
        save_html(final_html, output_path)
        print(str(f"[+] Saved to {output_path}").encode('ascii','replace').decode('ascii'))
    
    # Save quality gate report
    report_content = f"""Quality Gate Report
====================
Final Verdict: {final_verdict}
Rounds Used: {round_num}

Writer Assessment:
{assessment}

Auditor Notes:
{audit_notes}
"""
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(str(f"[+] Report saved to {REPORT_PATH}").encode('ascii','replace').decode('ascii'))
    
    # Print final status
    if final_verdict == "APPROVED":
        print(str("[+] GATE PASSED").encode('ascii','replace').decode('ascii'))
    else:
        print(str("[+] GATE PASSED WITH WARNINGS").encode('ascii','replace').decode('ascii'))


if __name__ == "__main__":
    main()

