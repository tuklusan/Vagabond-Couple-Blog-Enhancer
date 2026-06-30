import os
import sys
import json
import re
from openai import OpenAI

def main():
    """
    Role: ENGLISH EDITOR/REVIEWER - reviews final blog post HTML for writing quality.
    """
    # Read the full HTML file
    html_path = "Temp/final_html.html"
    if not os.path.exists(html_path):
        print("Error: Temp/final_html.html not found.".encode('ascii', 'replace').decode('ascii'))
        sys.exit(1)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Load DeepSeek API key
    api_key_path = "Config/_SECRETS/deepseek-api-key.txt"
    deepseek_api_key = None
    if os.path.exists(api_key_path):
        with open(api_key_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    deepseek_api_key = line.split("=", 1)[1].strip()
                    break
    
    if not deepseek_api_key:
        print("Error: DEEPSEEK_API_KEY not found in Config/_SECRETS/deepseek-api-key.txt".encode('ascii', 'replace').decode('ascii'))
        sys.exit(1)
    
    # Load NVIDIA API key
    nvidia_api_key_path = "Config/_SECRETS/nvidia-api-keys.txt"
    nvidia_api_key = None
    if os.path.exists(nvidia_api_key_path):
        with open(nvidia_api_key_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("NVIDIA_API_KEY=") and not line.startswith("NVIDIA_API_KEY_CODING="):
                    nvidia_api_key = line.split("=", 1)[1].strip()
                    break
    
    if not nvidia_api_key:
        print("Error: NVIDIA_API_KEY not found in Config/_SECRETS/nvidia-api-keys.txt".encode('ascii', 'replace').decode('ascii'))
        sys.exit(1)
    
    # Review prompt
    review_prompt = f"""You are an expert English editor/reviewer for a travel blog. Review the following HTML content for:

1. **Writing Quality** (per travel blog standards):
   - Active voice usage
   - No cliches or overused phrases
   - Sensory language (sight, sound, smell, touch, taste)
   - Correct narrator perspective (we/us for group travel, I/me for solo)
   - Grammar, spelling, punctuation

2. **HTML Integrity**:
   - Check for unclosed tags (e.g., <div>, <p>, <a>, <img>)
   - Proper nesting of elements
   - Valid attribute syntax

3. **ld+json Schema Validity**:
   - JSON syntax correctness
   - Required fields present (e.g., @context, @type, name, description)
   - Proper data types

Provide feedback grouped as:
- **Critical**: Issues that must be fixed (broken HTML, invalid JSON, major writing errors)
- **Warning**: Issues that should be fixed (minor writing issues, potential improvements)
- **Info**: Suggestions for enhancement

If the content is clean with no issues, respond with exactly: LGTM

HTML Content:
{html_content}"""
    
    # Offload review to OpenRouter (free) with DeepSeek/NVIDIA fallback
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.claude'))
    import or_client
    try:
        review_text, provider = or_client.chat(
            [
                {"role": "system", "content": "You are an expert English editor/reviewer for travel blog content."},
                {"role": "user", "content": review_prompt},
            ],
            max_tokens=4000, temperature=0.2)
        print(("Using reviewer: " + provider).encode('ascii', 'replace').decode('ascii'))
    except Exception as e:
        print(("All reviewers failed: " + str(e)).encode('ascii', 'replace').decode('ascii'))
        sys.exit(1)

    with open("Temp/output_review.txt", 'w', encoding='utf-8') as f:
        f.write(review_text)
    print(review_text.encode('ascii', 'replace').decode('ascii'))
    if re.search(r'critical', review_text, re.IGNORECASE):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
