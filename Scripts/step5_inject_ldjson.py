import argparse
import json
import re

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', required=True, help='Post title')
    args = parser.parse_args()

    with open('Temp/rewritten_html.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Check for jump break markers (case insensitive)
    jump_break_pattern = r'<!--\s*more\s*-->'
    match = re.search(jump_break_pattern, html_content, re.IGNORECASE)
    jump_break_found = match is not None

    # Build the JSON-LD object
    json_ld = {
        "@context": "https://schema.org",
        "@type": "TravelAction",
        "name": args.title,
        "actionStatus": "CompletedActionStatus",
        "object": {
            "@type": "TouristDestination",
            "name": "FILL_IN_DESTINATION",
            "url": "FILL_IN_DESTINATION_URL"
        },
        "agent": {
            "@type": "Person",
            "name": "FILL_IN_AUTHOR_NAME"
        },
        "description": "FILL_IN_SHORT_DESCRIPTION"
    }

    # Serialize as pretty JSON
    json_ld_str = json.dumps(json_ld, indent=2, ensure_ascii=False)

    # Create the script tag
    script_tag = f"<script type='application/ld+json'>\n{json_ld_str}\n</script>"

    # Find insertion point
    if jump_break_found:
        # Insert before the jump break
        start_pos = match.start()
        result = html_content[:start_pos] + script_tag + "\n" + html_content[start_pos:]
        print("Jump break found")
    else:
        # Prepend to the beginning of the document
        result = script_tag + "\n" + html_content
        print("Jump break not found")

    # Write the result to file
    with open('Temp/final_html.html', 'w', encoding='utf-8') as f:
        f.write(result)

if __name__ == "__main__":
    main()