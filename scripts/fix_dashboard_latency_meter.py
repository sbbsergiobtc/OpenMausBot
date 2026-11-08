import re

path = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# 1. Add checkFeedPing right after updateDaemonHealth
target1 = """          if (hlText) hlText.innerText = 'Websockets en reconexión...';
        }
      }
    }"""

# Use regex to match safely
func_regex = r'(function updateDaemonHealth\(status, latencyMs\)\s*\{.*?\}\s*\})'
m = re.search(func_regex, text, flags=re.DOTALL)
if m:
    old_func = m.group(1)
    new_func = old_func + """

    // Medición exacta y ligera de latencia Heartbeat/Ping (RTT)
    async function checkFeedPing() {
      const t0 = performance.now();
      try {
        const res = await fetch('/api/ping');
        if (res.ok) {
          const rtt = Math.max(5, Math.round(performance.now() - t0));
          updateDaemonHealth('online', rtt);
        } else {
          updateDaemonHealth('reconnecting');
        }
      } catch (err) {
        updateDaemonHealth('reconnecting');
      }
    }"""
    text = text.replace(old_func, new_func, 1)
    print("1. checkFeedPing inserted successfully")
else:
    print("1. ERROR: updateDaemonHealth not found")

# 2. In fetchCurrentDashboard: do not overwrite latency with the 11-request batch time!
old_batch = """        const anyOk = results.some(r => r.status === 'fulfilled');
        if (anyOk) {
          const lat = Math.max(5, Math.round(performance.now() - startT));
          updateDaemonHealth('online', lat);
        } else {
          updateDaemonHealth('reconnecting');
        }"""

new_batch = """        const anyOk = results.some(r => r.status === 'fulfilled');
        if (anyOk) {
          checkFeedPing();
        } else {
          updateDaemonHealth('reconnecting');
        }"""

if old_batch in text:
    text = text.replace(old_batch, new_batch, 1)
    print("2. fetchCurrentDashboard ping fixed")
else:
    print("2. Trying regex for fetchCurrentDashboard batch")
    text = re.sub(
        r'const anyOk = results\.some\(r => r\.status === \'fulfilled\'\);\s*if \(anyOk\) \{\s*const lat = Math\.max\(5, Math\.round\(performance\.now\(\) - startT\)\);\s*updateDaemonHealth\(\'online\', lat\);\s*\} else \{\s*updateDaemonHealth\(\'reconnecting\'\);\s*\}',
        new_batch,
        text
    )

# 3. In fetchForwardState and fetchTelemetry: do not overwrite lightweight ping with large payload download times
text = re.sub(
    r'const lat = Math\.max\(5, Math\.round\(performance\.now\(\) - startT\)\);\s*updateDaemonHealth\(\'online\', lat\);',
    r'// Payload recibido OK - el ping ligero se gestiona via checkFeedPing\n        if (!isDaemonOnline) checkFeedPing();',
    text
)
print("3. Heavy payload latency overrides removed")

# 4. In DOMContentLoaded: start checkFeedPing interval (every 5 seconds)
old_dom = "fetchAccountStage();\n      fetchNotifications();"
new_dom = "checkFeedPing();\n      setInterval(checkFeedPing, 5000);\n      fetchAccountStage();\n      fetchNotifications();"

if old_dom in text:
    text = text.replace(old_dom, new_dom, 1)
    print("4. checkFeedPing added to DOMContentLoaded")
else:
    print("4. Trying regex for DOMContentLoaded")
    text = re.sub(r'fetchAccountStage\(\);\s*fetchNotifications\(\);', new_dom, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("index.html latency optimizations applied!")
