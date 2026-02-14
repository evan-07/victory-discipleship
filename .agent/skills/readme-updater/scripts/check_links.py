import re
import os

def check_readme_links():
    with open("README.md", "r") as f:
        content = f.read()
    
    # Find all local markdown links: [text](path/to/file)
    links = re.findall(r'\[.*?\]\((?!http)(.*?)\)', content)
    
    broken_links = []
    for link in links:
        # Strip anchors like #section
        clean_link = link.split('#')[0]
        if clean_link and not os.path.exists(clean_link):
            broken_links.append(clean_link)
            
    if broken_links:
        print("❌ BROKEN LINKS DETECTED:")
        for l in broken_links:
            print(f"  - {l}")
    else:
        print("✅ All local links in README are valid.")

if __name__ == "__main__":
    check_readme_links()