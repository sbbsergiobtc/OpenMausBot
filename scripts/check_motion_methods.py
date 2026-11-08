import urllib.request

url = 'https://cdn.jsdelivr.net/npm/motion@11.11.17/dist/motion.js'
content = urllib.request.urlopen(url).read().decode('utf-8')

# Search for "finished" in motion.js
print("Does 'finished' exist in motion.js?", "finished" in content)
# Search for animate
print("Does '.animate' exist in motion.js?", ".animate" in content)
