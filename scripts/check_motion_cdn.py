import urllib.request
import re

url = 'https://cdn.jsdelivr.net/npm/motion@11.11.17/dist/motion.js'
content = urllib.request.urlopen(url).read().decode('utf-8')
print("Length:", len(content))
print("First 300 chars:")
print(content[:300])
# look for window or global assignments
globals_found = re.findall(r'(?:window\.|globalThis\.|exports\.)([a-zA-Z0-9_$]+)', content)
print("Globals found:", list(set(globals_found))[:10])
