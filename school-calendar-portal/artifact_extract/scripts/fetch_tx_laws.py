"""
Fetch Texas Family Code sections related to ESPO (Standard Possession Order)
and SPO (Shared Possession Order) custody schedules.

Relevant statutes:
- §153.001 - Public Policy
- §153.002 - Best Interest of Child  
- §153.312 - Possessory Conservator: Rights and Duties
- §153.314 - Holiday Possession Unaffected by Distance
- §153.315 - Weekend Possession Extended by Holiday
- §153.316 - General Terms and Conditions
- §153.317 - Alternative Beginning and Ending Possession Times
- §153.075 - Duties of Parent Not Appointed Conservator
"""
import sys
import urllib.request
import json

SECTIONS = {
    '153.001': 'Public Policy',
    '153.002': 'Best Interest of Child',
    '153.312': 'Possessory Conservator Rights and Duties',
    '153.314': 'Holiday Possession Unaffected by Distance',
    '153.315': 'Weekend Possession Extended by Holiday',
    '153.316': 'General Terms and Conditions',
    '153.317': 'Alternative Beginning and Ending Possession Times',
    '153.075': 'Duties of Parent Not Appointed Conservator',
}

BASE_URL = 'https://texas.public.law/statutes/tex._fam._code_section_{}'

def fetch_section(section_num):
    """Fetch a Texas Family Code section from texas.public.law."""
    url = BASE_URL.format(section_num)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; CoParentingBot/1.0)'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
    return content

def extract_statute_text(html_content):
    """Extract clean statute text from HTML."""
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Try to extract the statute section
    # Look for the law text between markers
    start = text.find('The following provisions govern')
    if start == -1:
        start = text.find('possession of the child')
    if start == -1:
        return text[max(0, len(text)//2):len(text)//2+5000]
    return text[start:start+8000]

def save_laws(output_path='tx_custody_laws.md'):
    """Fetch all relevant Texas custody statutes and save to markdown."""
    all_content = ['# Texas Family Code - Child Possession Laws\n',
                   '_Auto-generated from texas.public.law_\n',
                   '_§153.314 Holiday Possession is the primary statute for co-parenting calendars_\n\n']
    
    for section, title in SECTIONS.items():
        print(f"Fetching §{section} - {title}...")
        try:
            html = fetch_section(section)
            text = extract_statute_text(html)
            all_content.append(f'## §{section} -- {title}\n\n')
            all_content.append(text[:5000])
            all_content.append('\n\n---\n\n')
        except Exception as e:
            print(f"  ERROR fetching §{section}: {e}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(all_content))
    print(f"\nSaved to {output_path}")

if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'tx_custody_laws.md'
    save_laws(output)
