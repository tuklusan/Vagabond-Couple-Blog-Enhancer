import json
import os
import sys

import requests


def main():
    try:
        # 1. Parse JSON from stdin
        raw_stdin = sys.stdin.read()
        hook_input = json.loads(raw_stdin)
        file_path = hook_input.get("tool_input", {}).get("file_path", "")

        # 2. Skip conditions
        if not file_path:
            return
        if file_path.startswith("Doc/") or "/Doc/" in file_path:
            return
        if file_path.endswith(".review.txt"):
            return
        if "_SECRETS" in file_path:
            return
        if "check_and_update_docs" in file_path:
            return

        # Path traversal protection
        cwd = os.getcwd()
        abs_file = os.path.abspath(file_path)
        if not abs_file.startswith(os.path.join(cwd, "")):
            safe_print("[docs] Error: path not within project root")
            return

        if not os.path.isfile(file_path):
            return

        # 3. Read changed file content, cap at 3000 chars
        with open(file_path, "r", encoding="utf-8") as f:
            changed_content = f.read(3000)

        # 4. Read Doc/DESIGN.txt
        design_path = "Doc/DESIGN.txt"
        if os.path.isfile(design_path):
            with open(design_path, "r", encoding="utf-8") as f:
                current_design = f.read()
        else:
            current_design = ""

        # 5. Read Doc/WORKFLOW.md
        workflow_path = "Doc/WORKFLOW.md"
        if os.path.isfile(workflow_path):
            with open(workflow_path, "r", encoding="utf-8") as f:
                current_workflow = f.read()
        else:
            current_workflow = ""

        # 6. Load DeepSeek API key
        secrets_path = "Config/_SECRETS/deepseek-api-key.txt"
        api_key = ""
        if os.path.isfile(secrets_path):
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        break
        if not api_key:
            safe_print("[docs] Error: DeepSeek API key not found")
            return

        # 7. Build prompt
        # Use unique delimiters unlikely to appear in documentation
        DESIGN_MARKER = "!!DESIGN_UPDATE!!"
        WORKFLOW_MARKER = "!!WORKFLOW_UPDATE!!"
        prompt = (
            "You are a technical documentation maintainer.\n"
            "The file that was changed: " + file_path + "\n\n"
            "Current Doc/DESIGN.txt content:\n"
            + current_design + "\n\n"
            "Current Doc/WORKFLOW.md content:\n"
            + current_workflow + "\n\n"
            "Changed file content:\n"
            + changed_content + "\n\n"
            "Does this change require updates to DESIGN.txt or WORKFLOW.md?\n"
            "If YES: respond with exactly one or both of the following markers on their own lines:\n"
            + DESIGN_MARKER + " followed by the full new DESIGN.txt content\n"
            + WORKFLOW_MARKER + " followed by the full new WORKFLOW.md content\n"
            "You must output the markers at the start of a line exactly as shown. "
            "Do not include any additional text before the first marker.\n"
            "If NO updates are needed, respond with exactly \"NO_UPDATE_NEEDED\"."
        )

        # 8. Call DeepSeek API
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-v4-pro",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 8192,
        }
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        response_data = resp.json()
        response_text = response_data["choices"][0]["message"]["content"]

        # 9. Parse response using position-based extraction
        if "NO_UPDATE_NEEDED" in response_text:
            safe_print("[docs] No update needed.")
        else:
            # Find all marker occurrences and their positions
            markers = {
                DESIGN_MARKER: design_path,
                WORKFLOW_MARKER: workflow_path,
            }
            positions = {}
            for marker, path in markers.items():
                idx = response_text.find(marker)
                if idx != -1:
                    positions[idx] = marker

            if not positions:
                safe_print("[docs] No update needed.")
            else:
                # Sort by position
                sorted_positions = sorted(positions.items())  # [(pos, marker), ...]
                num = len(sorted_positions)
                for i, (pos, marker) in enumerate(sorted_positions):
                    start = pos + len(marker)
                    if i + 1 < num:
                        end = sorted_positions[i + 1][0]
                    else:
                        end = len(response_text)
                    content = response_text[start:end].strip()
                    if content:
                        output_path = markers[marker]
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        if output_path == design_path:
                            safe_print("[docs] Updated Doc/DESIGN.txt")
                        elif output_path == workflow_path:
                            safe_print("[docs] Updated Doc/WORKFLOW.md")

    except Exception as e:
        safe_print("[docs] Error: " + str(e))

    sys.exit(0)


def safe_print(msg):
    print(str(msg).encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()