import sys
import json
import os
import re
import requests

def safe_print(msg):
    print(str(msg).encode('ascii', 'replace').decode('ascii'))

def main():
    try:
        # 1. Read and parse JSON from stdin
        raw = sys.stdin.read()
        hook_data = json.loads(raw)

        # Only act on Write or Edit tools
        tool_name = hook_data.get('tool_name')
        if tool_name not in ('Write', 'Edit'):
            return

        # Gracefully handle missing tool_input
        if 'tool_input' not in hook_data:
            safe_print("[docs] Missing tool_input in hook data.")
            return
        file_path = hook_data['tool_input'].get('file_path')
        if not file_path:
            safe_print("[docs] No file_path provided.")
            return

        # 2. Apply skip conditions
        if file_path.startswith('Doc/') or '/Doc/' in file_path:
            return
        if file_path.endswith('.review.txt'):
            return
        if '_SECRETS' in file_path:
            return
        if 'check_and_update_docs' in file_path:
            return
        if not os.path.isfile(file_path):
            return

        # 3. Read changed file content (cap at 3000 chars)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                changed_content = f.read(3000)
        except Exception:
            return

        # 4. Read Doc/DESIGN.txt
        design_path = 'Doc/DESIGN.txt'
        if not os.path.isfile(design_path):
            design_content = ''
        else:
            with open(design_path, 'r', encoding='utf-8') as f:
                design_content = f.read()

        # 5. Read Doc/WORKFLOW.md
        workflow_path = 'Doc/WORKFLOW.md'
        if not os.path.isfile(workflow_path):
            workflow_content = ''
        else:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_content = f.read()

        # 7. Build prompt using pure string concatenation (no %-formatting)
        prompt = (
            "You are a technical documentation maintainer.\n"
            "File changed: " + file_path + "\n\n"
            "Current DESIGN.txt content:\n" + design_content + "\n\n"
            "Current WORKFLOW.md content:\n" + workflow_content + "\n\n"
            "Changed file content:\n" + changed_content + "\n\n"
            "Does this change require updates to DESIGN.txt or WORKFLOW.md?\n"
            "If yes, respond with marker DESIGN_UPDATE: followed by full new DESIGN.txt content, "
            "and/or WORKFLOW_UPDATE: followed by full new WORKFLOW.md content.\n"
            "If no, respond with exactly NO_UPDATE_NEEDED."
        )

        # 8. Offload doc-impact analysis to OpenRouter (DeepSeek/NVIDIA fallback)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import or_client
        try:
            response_text, _ = or_client.chat(
                [{'role': 'user', 'content': prompt}], max_tokens=8192)
        except Exception as e:
            safe_print("[docs] review providers failed: " + str(e))
            return

        # 9. Parse response with strict NO_UPDATE_NEEDED check
        if response_text.strip() == 'NO_UPDATE_NEEDED':
            safe_print("[docs] No update needed.")
        else:
            # Extract content for each possible marker using regex
            pattern = r'(DESIGN_UPDATE:|WORKFLOW_UPDATE:)(.*?)(?=(?:DESIGN_UPDATE:|WORKFLOW_UPDATE:)|$)'
            matches = re.findall(pattern, response_text, re.DOTALL)

            design_update = None
            workflow_update = None
            for marker, content in matches:
                if marker == 'DESIGN_UPDATE:':
                    design_update = content.strip()
                elif marker == 'WORKFLOW_UPDATE:':
                    workflow_update = content.strip()

            updated_any = False
            if design_update is not None:
                with open(design_path, 'w', encoding='utf-8') as f:
                    f.write(design_update)
                safe_print("[docs] Updated Doc/DESIGN.txt")
                updated_any = True
            if workflow_update is not None:
                with open(workflow_path, 'w', encoding='utf-8') as f:
                    f.write(workflow_update)
                safe_print("[docs] Updated Doc/WORKFLOW.md")
                updated_any = True
            if not updated_any:
                safe_print("[docs] No update markers found in response.")
    except Exception as e:
        safe_print("[docs] Error: " + str(e))

if __name__ == '__main__':
    main()
    sys.exit(0)