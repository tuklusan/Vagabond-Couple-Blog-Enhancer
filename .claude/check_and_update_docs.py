import json
import os
import sys
import traceback
import requests

def main():
    try:
        # Read hook JSON from stdin
        raw = sys.stdin.read()
        hook = json.loads(raw)
        tool_input = hook.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        # Skip certain paths
        if not file_path:
            print("[docs] No file_path in hook input. Skipping.")
            return

        # Normalize path
        file_path = os.path.normpath(file_path)

        # Skip Doc/ files, .review.txt files, Config/_SECRETS/ files
        if file_path.startswith("Doc" + os.sep) or file_path.startswith("Doc/") \
                or file_path.endswith(".review.txt") \
                or ("Config/_SECRETS" + os.sep) in file_path or ("Config/_SECRETS/") in file_path:
            print("[docs] Skipping excluded path: " + file_path)
            return

        # Read changed file content from disk
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                changed_content = f.read()
        except Exception as e:
            print("[docs] Error reading changed file: " + str(e))
            return

        # Read current DESIGN.txt and WORKFLOW.md
        design_path = os.path.join("Doc", "DESIGN.txt")
        workflow_path = os.path.join("Doc", "WORKFLOW.md")

        design_content = ""
        if os.path.exists(design_path):
            with open(design_path, 'r', encoding='utf-8') as f:
                design_content = f.read()

        workflow_content = ""
        if os.path.exists(workflow_path):
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_content = f.read()

        # Truncate changed content to 3000 chars
        truncated_changed = changed_content[:3000]  # can be shorter

        # Construct prompt
        prompt = f"""You are a technical documentation maintainer.
A file was just changed: {file_path}
Current DESIGN.txt:
{design_content[:3000] if design_content else "(empty)"}
Current WORKFLOW.md:
{workflow_content[:3000] if workflow_content else "(empty)"}
Changed file content:
{truncated_changed if truncated_changed else "(empty)"}
Question: Does this change require updates to DESIGN.txt or WORKFLOW.md?
If YES: respond with DESIGN_UPDATE: followed by the FULL updated DESIGN.txt, then WORKFLOW_UPDATE: followed by the FULL updated WORKFLOW.md (only include sections that changed, others unchanged)
If NO: respond with just: NO_UPDATE_NEEDED"""

        # Load DeepSeek API key
        key_path = os.path.join("Config", "_SECRETS", "deepseek-api-key.txt")
        api_key = None
        try:
            with open(key_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
        except Exception as e:
            print("[docs] Error reading API key: " + str(e))
            return

        if not api_key:
            print("[docs] No DEEPSEEK_API_KEY found.")
            return

        # Call DeepSeek API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-v4-pro",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4096,
            "temperature": 0.0
        }
        try:
            resp = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            if resp.status_code != 200:
                print("[docs] API request failed: HTTP " + str(resp.status_code) + " " + resp.text)
                return
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
        except Exception as e:
            print("[docs] API call error: " + str(e))
            return

        # Parse response
        reply = reply.strip()

        if "NO_UPDATE_NEEDED" in reply and "DESIGN_UPDATE:" not in reply and "WORKFLOW_UPDATE:" not in reply:
            print("[docs] No documentation update needed.")
            return

        updated_design = None
        updated_workflow = None

        # Find DESIGN_UPDATE: section
        if "DESIGN_UPDATE:" in reply:
            idx = reply.find("DESIGN_UPDATE:")
            # Extract everything after that until WORKFLOW_UPDATE: or end
            remaining = reply[idx + len("DESIGN_UPDATE:"):]
            # If there is WORKFLOW_UPDATE: later, split
            if "WORKFLOW_UPDATE:" in remaining:
                wf_idx = remaining.find("WORKFLOW_UPDATE:")
                updated_design = remaining[:wf_idx].strip()
                # Remove potential leading/trailing whitespace
                # For the workflow part, extract after WORKFLOW_UPDATE:
                updated_workflow = remaining[wf_idx + len("WORKFLOW_UPDATE:"):].strip()
            else:
                updated_design = remaining.strip()
                updated_workflow = None
        elif "WORKFLOW_UPDATE:" in reply:
            # Only workflow update
            idx = reply.find("WORKFLOW_UPDATE:")
            updated_workflow = reply[idx + len("WORKFLOW_UPDATE:"):].strip()
            updated_design = None

        # If we have updates, write them to files
        any_update = False
        if updated_design is not None and updated_design:
            try:
                os.makedirs("Doc", exist_ok=True)
                with open(design_path, 'w', encoding='utf-8') as f:
                    f.write(updated_design)
                print("[docs] Updated: DESIGN.txt")
                any_update = True
            except Exception as e:
                print("[docs] Error writing DESIGN.txt: " + str(e))

        if updated_workflow is not None and updated_workflow:
            try:
                os.makedirs("Doc", exist_ok=True)
                with open(workflow_path, 'w', encoding='utf-8') as f:
                    f.write(updated_workflow)
                print("[docs] Updated: WORKFLOW.md")
                any_update = True
            except Exception as e:
                print("[docs] Error writing WORKFLOW.md: " + str(e))

        if not any_update:
            print("[docs] No documentation update needed (parsed response indicates no update).")
    except Exception as e:
        # Catch-all for unexpected errors
        print("[docs] Unexpected error: " + str(e))
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    main()
    sys.exit(0)