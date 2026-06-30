import os
import time
from openai import OpenAI

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def read_api_key():
    with open('Config/_SECRETS/nvidia-api-keys.txt', 'r') as f:
        for line in f:
            if line.startswith('NVIDIA_API_KEY=') and not line.startswith('NVIDIA_API_KEY_CODING='):
                return line.split('=', 1)[1].strip()
    raise ValueError("NVIDIA_API_KEY not found in Config/_SECRETS/nvidia-api-keys.txt")

def main():
    # Read files
    prose_blocks = read_file('Temp/prose_blocks.txt')
    writing_rules = read_file('Config/writing_rules.md')
    
    # Read API key
    api_key = read_api_key()
    
    # Prepare prompts
    system_prompt = """NARRATOR: The blog is written by The Vagabond Couple. ALWAYS use 'we', 'us', 'our'. NEVER use 'I', 'me', 'my', 'mine'. Scan your output and fix every violation before returning.
BLOCK COUNT: You will receive N numbered blocks [0] through [N-1]. You MUST return exactly N blocks with the same [N] prefix. Never merge, split, add, or drop blocks.
FORMAT: Return ONLY the numbered list. No preamble. No explanation. No markdown.

You are a travel blog editor. Rewrite each numbered prose block according to the writing rules. Preserve the [N] prefix where N is the block number. Do not merge or split blocks. Return only the numbered list."""
    
    user_prompt = f"WRITING RULES:\n{writing_rules}\n\nPROSE BLOCKS:\n{prose_blocks}"
    
    # Offload rewrite to OpenRouter (free) with DeepSeek/NVIDIA fallback
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.claude'))
    import or_client
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    rewritten_content, _provider = or_client.chat(messages, max_tokens=8192, temperature=0.3)
    print(f"Rewriter provider: {_provider}")
    
    # Save to file
    with open('Temp/rewritten_blocks.txt', 'w', encoding='utf-8') as f:
        f.write(rewritten_content)
    
    # Print stats
    print(f"Characters sent: {len(system_prompt) + len(user_prompt)}")
    print(f"Characters received: {len(rewritten_content)}")

if __name__ == "__main__":
    main()
