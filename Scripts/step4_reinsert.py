import re
from bs4 import BeautifulSoup

def read_rewrites(rewritten_blocks_path):
    rewrites = {}
    with open(rewritten_blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.match(r'\[(\d+)\](.*)', line)
            if match:
                index = int(match.group(1))
                text = match.group(2).strip()
                rewrites[index] = text
    return rewrites

def extract_text_blocks(soup):
    tags = { 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote' }
    text_blocks = []
    for tag in soup.find_all(tags):
        if tag.get_text(strip=True):
            parents = tag.find_parents(['script', 'style'])
            if not parents:
                text_blocks.append(tag)
    return text_blocks

def main():
    prose_blocks_path = 'Temp/prose_blocks.txt'
    rewritten_blocks_path = 'Temp/rewritten_blocks.txt'
    html_path = 'Input/Dundee_Bay__Grand_Bahama__A_Complete_Guide_to_This_Hidden_Ca__ORIGINAL.html'
    output_path = 'Temp/rewritten_html.html'
    
    rewrites = read_rewrites(rewritten_blocks_path)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    text_blocks = extract_text_blocks(soup)
    
    rewritten_count = 0
    for i, tag in enumerate(text_blocks):
        if i in rewrites:
            tag.clear()
            tag.append(rewrites[i])
            rewritten_count += 1
    
    for i in range(len(text_blocks)):
        if i not in rewrites:
            continue
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Blocks reinserted: {rewritten_count}")

if __name__ == "__main__":
    main()