import json
import sys
import os

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        
        hook_data = json.loads(raw_input)
        
        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})
        if tool_name not in ("Write", "Edit"):
            sys.exit(0)
        file_path = tool_input.get("file_path", "")
        
        if not isinstance(file_path, str) or not file_path:
            sys.exit(0)
        
        if not file_path.endswith(".py"):
            sys.exit(0)
        
        if "code_agent" in file_path:
            sys.exit(0)
        
        result = {
            "decision": "block",
            "reason": "Python files must be written via .claude/code_agent.py, not directly by Claude. Use the command: .claude/code_agent.py to generate Python code."
        }
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception:
        sys.exit(0)

if __name__ == "__main__":
    main()