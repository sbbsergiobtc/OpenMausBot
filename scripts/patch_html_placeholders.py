from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
INDEX_PATH = BASE_DIR / "dashboard" / "templates" / "index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Update initial HTML for Card 1
content = content.replace(
    '<div class="text-lg sm:text-2xl font-bold font-mono text-[#1D1D1F] tracking-tight" id="cockpit-kpi-total-balance">$1,998.09</div>',
    '<div class="text-lg sm:text-2xl font-bold font-mono text-[#1D1D1F] tracking-tight" id="cockpit-kpi-total-balance">$24,998.09</div>'
)
content = content.replace(
    '<span id="cockpit-kpi-total-subtext" class="badge-brand-indigo font-mono text-[10px] py-0.5 px-1.5">MT5 + DEX</span>',
    '<span id="cockpit-kpi-total-subtext" class="badge-brand-indigo font-mono text-[10px] py-0.5 px-1.5">25 Cuentas x $1k</span>'
)
content = content.replace(
    '<span id="cockpit-sync-badge" class="badge-success-live font-mono">● 2 CUENTAS CONECTADAS</span>',
    '<span id="cockpit-sync-badge" class="badge-success-live font-mono">● 25 CUENTAS FT</span>'
)
content = content.replace(
    'Supervisión consolidada de capital propio en Forward Test: IC Markets (MT5 $1,000) y Hyperliquid (Crypto DEX 1,000 USDC).',
    'Supervisión consolidada de capital propio en Forward Test: 25 estrategias ($25,000 inicial) en MT5 Demo y Hyperliquid DEX.'
)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated initial HTML placeholders for aggregate balance!")
