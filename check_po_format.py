import re
with open('locale/en/LC_MESSAGES/messages.po', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'msgctxt\s+"[^"]+"\s*\nmsgid\s+"[^"]+"\s*\nmsgstr\s+"[^"]*"', content)
if match:
    print('Sample block:')
    print(match.group(0)[:300])