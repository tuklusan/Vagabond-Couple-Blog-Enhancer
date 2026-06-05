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
    
    # Try DeepSeek first
    try:
        print("Using reviewer: deepseek-v4-pro (api.deepseek.com)")
        client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": "You are an expert English editor/reviewer for travel blog content."},
                {"role": "user", "content": review_prompt}
            ],
            temperature=0.2,
            max_tokens=4000
        )
        
        review_text = response.choices[0].message.content
        
        # Save review to file
        output_path = "Temp/output_review.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(review_text)
        
        # Print review
        print(review_text.encode('ascii', 'replace').decode('ascii'))
        
        # Check for critical issues
        if re.search(r'critical', review_text, re.IGNORECASE):
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"DeepSeek review failed: {str(e)}".encode('ascii', 'replace').decode('ascii'))
        print("Falling back to NVIDIA reviewer...")
        
        # Try NVIDIA fallback
        try:
            print("Using reviewer: meta/llama-3.1-70b-instruct (integrate.api.nvidia.com)")
            client = OpenAI(
                api_key=nvidia_api_key,
                base_url="https://integrate.api.nvidia.com/v1"
            )
            response = client.chat.completions.create(
                model="meta/llama-3.1-70b-instruct",
                messages=[
                    {"role": "system", "content": "You are an expert English editor/reviewer for travel blog content."},
                    {"role": "user", "content": review_prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            review_text = response.choices[0].message.content
            
            # Save review to file
            output_path = "Temp/output_review.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(review_text)
            
            # Print review
            print(review_text.encode('ascii', 'replace').decode('ascii'))
            
            # Check for critical issues
            if re.search(r'critical', review_text, re.IGNORECASE):
                sys.exit(1)
            else:
                sys.exit(0)
                
        except Exception as e2:
            print(f"Both reviewers failed. DeepSeek error: {str(e)}".encode('ascii', 'replace').decode('ascii'))
            print(f"NVIDIA error: {str(e2)}".encode('ascii', 'replace').decode('ascii'))
            sys.exit(1)

if __name__ == "__main__":
    main()
