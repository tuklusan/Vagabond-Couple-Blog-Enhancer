import os
from bs4 import BeautifulSoup

# Create Temp/ directory if it doesn't exist
temp_dir = 'Temp'
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# Read the HTML file
input_file = 'Input/Dundee_Bay__Grand_Bahama__A_Complete_Guide_to_This_Hidden_Ca__ORIGINAL.html'
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Parse with BeautifulSoup
soup = BeautifulSoup(content, 'html.parser')

# Remove script and style elements
for script_or_style in soup.find_all(['script', 'style']):
    script_or_style.decompose()

# Find all specified tags with non-empty text
target_tags = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'}
blocks = []

# Find all tags and filter by tag name and text content
for tag in soup.find_all(True):
    if tag.name in target_tags and tag.get_text(strip=True):
        text = tag.get_text(separator=' ', strip=True)
        if text:  # Only include if text is not empty
            blocks.append(text)

# Create numbered list
numbered_blocks = [f"[{i+1}] {text}" for i, text in enumerate(blocks)]

# Write to file
output_file = os.path.join(temp_dir, 'prose_blocks.txt')
with open(output_file, 'w', encoding='utf-8') as f:
    for block in numbered_blocks:
        f.write(block + '\n')

# Print statistics
total_blocks = len(numbered_blocks)
total_chars = sum(len(block) for block in blocks)
print(f"Total blocks: {total_blocks}")
print(f"Total characters: {total_chars}")