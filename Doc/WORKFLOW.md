# Project Workflow

## Permissions

Claude has blanket permission to run any shell commands needed to implement, test,
and validate work on this project without asking for confirmation first.

## Storage Rules

- ALL intermediate files, temp scripts, and review outputs go to the project `Temp/` directory.
- `AppData`, system temp (`%TEMP%`, `%TMP%`), or any path outside the project directory must NEVER be used.
- **BACKGROUND TASKS ARE BANNED.** Never use `run_in_background`, never use background job operators. All commands run in the foreground. Violation routes output to AppData instead of the terminal.

---

## Roles

| Role | Agent | Responsibilities |
|------|-------|-----------------|
| **Coder** | `qwen/qwen3-coder-480b-a35b-instruct` via NVIDIA NIM | Writes ALL Python code and fixes |
| **Code Reviewer** | `deepseek-v4-pro` via api.deepseek.com | Reviews ALL code before it is used |
| **Executor / Orchestrator** | Claude | Runs the pipeline, calls agents, delivers results — does NOT write or review code |

Claude never writes Python code directly. When code is needed, Claude calls `.claude/code_agent.py`,
which runs the Qwen → DeepSeek review loop (up to 3 rounds) and outputs approved code.

---

## Design Document Rule

**`Doc/DESIGN.txt` must be updated before or alongside any change that affects:**
- Directory layout
- Pipeline steps or their order
- Input/output file formats or naming conventions
- External integrations (APIs, services, auth)
- Scope constraints (e.g., "no automatic uploads")
- CLI interface (flags, defaults)

The design document is the source of truth. Code must conform to it. If a code change requires a design change, update `DESIGN.txt` first, then implement.

---

## Delivery Checklist

Every code or documentation change must pass through these steps **in order** before being considered delivered:

### 1. Implement
- Write or edit code / documentation
- Ensure the change conforms to `Doc/DESIGN.txt`
- Update `Doc/DESIGN.txt` if the design has evolved

### 2. DeepSeek Review
- Submit all changed files to DeepSeek using the `DEEPSEEK_API_KEY`
- Ask DeepSeek to review for:
  - **Code:** correctness, edge cases, security, style, conformance to design
  - **Docs:** accuracy, completeness, consistency with current code
- Capture all issues DeepSeek raises

### 3. Fix
- Address every issue DeepSeek identified
- Re-submit the fixed version to DeepSeek if issues were substantive
- Iterate until DeepSeek raises no blocking issues

### 4. Deliver
- Confirm `Doc/DESIGN.txt` reflects the final state
- Present the finished change to the user

---

## Model Pipeline

All AI calls use NVIDIA NIM (`https://integrate.api.nvidia.com/v1`) via the OpenAI-compatible API.
Keys are stored in `Config/nvidia-api-keys.txt`.

| Role | Model | Key |
|------|-------|-----|
| Blog prose rewrite | `meta/llama-3.1-70b-instruct` | `NVIDIA_API_KEY` |
| Primary coder | `deepseek-v4-pro` | `DEEPSEEK_API_KEY` (api.deepseek.com) |
| Fallback coder | `nvidia/nemotron-3-super-120b-a12b` | `NVIDIA_API_KEY_CODING` (NVIDIA NIM) |
| Primary code reviewer | `deepseek-v4-pro` | `DEEPSEEK_API_KEY` (api.deepseek.com) |
| Fallback code reviewer | `qwen/qwen3-coder-480b-a35b-instruct` | `NVIDIA_API_KEY_CODING` (NVIDIA NIM) |

## Code Review — How to Call

```python
from openai import OpenAI

def deepseek_review(changed_files: dict[str, str], context: str = "") -> str:
    """
    changed_files: {filename: file_contents}
    context: brief description of what changed and why
    """
    client = OpenAI(
        api_key=_load_deepseek_key(),   # Config/deepseek-api-key.txt or DEEPSEEK_API_KEY env
        base_url="https://api.deepseek.com",
    )
    file_block = "\n\n".join(
        f"### {name}\n```\n{contents}\n```"
        for name, contents in changed_files.items()
    )
    prompt = (
        f"You are a code reviewer. Context: {context}\n\n"
        f"Review the following for correctness, security, style, and design "
        f"consistency. List every issue grouped by severity. Say LGTM if clean.\n\n"
        f"{file_block}"
    )
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.1,
    )
    return response.choices[0].message.content
```

---

## Revision Numbering

Script filenames carry a revision suffix: `...-rev000.py`, `...-rev001.py`, etc.
Increment the revision number on each delivery that modifies the script.
Documentation files do not carry revision numbers — use git history or timestamps.
