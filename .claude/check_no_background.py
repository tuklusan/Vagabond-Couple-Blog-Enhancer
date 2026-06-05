import sys
import json

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
        tool_input = data.get("tool_input", {})
        if tool_input.get("run_in_background", False) is True:
            msg = "Background tasks are banned in this project. All commands must run in the foreground. See Doc/WORKFLOW.md."
            safe_msg = str(msg).encode('ascii', 'replace').decode('ascii')
            result = {"decision": "block", "reason": safe_msg}
            safe_result = str(json.dumps(result)).encode('ascii', 'replace').decode('ascii')
            print(safe_result)
        sys.exit(0)
    except Exception:
        sys.exit(0)

if __name__ == "__main__":
    main()