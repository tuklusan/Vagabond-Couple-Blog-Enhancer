import argparse
import re
import os
from datetime import datetime

def get_safe_title(title):
    return re.sub(r'[^\w\-]', '_', title)[:60]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', required=True, help='Title for the HTML file')
    args = parser.parse_args()
    
    safe_title = get_safe_title(args.title)
    
    input_file = f"Input/{safe_title}__ORIGINAL.html"
    temp_file = "Temp/final_html.html"
    
    # Read the original HTML file
    with open(input_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Read the final HTML content
    with open(temp_file, 'r', encoding='utf-8') as f:
        final_content = f.read()
    
    # Create Output directory if it doesn't exist
    os.makedirs("Output", exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output filename
    output_filename = f"Output/{safe_title}__{timestamp}.html"
    
    # Write the content to the output file
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(output_filename)

if __name__ == "__main__":
    main()