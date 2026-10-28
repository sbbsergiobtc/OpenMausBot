from pathlib import Path

tmpl_path = Path('/root/AlgrokQuant/dashboard/templates/index.html')
content = tmpl_path.read_text(encoding='utf-8')

# 1. Modificar el header del modal para añadir el botón de TradingView
old_header = """      <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-dark-950/80 rounded-t-2xl">
        <h3 class="font-bold text-white font-mono flex items-center" id="modal-title">Ficha Técnica</h3>
        <button onclick="closeModal()" class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>"""

new_header = """      <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-dark-950/80 rounded-t-2xl">
        <h3 class="font-bold text-white font-mono flex items-center" id="modal-title">Ficha Técnica</h3>
        <div class="flex items-center gap-2">
          <button id="modal-tv-btn" onclick="openCurrentStrategyFromModal()" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 transition flex items-center gap-1.5 shadow-sm">
            <i class="fa-solid fa-chart-line text-emerald-400"></i> Ver en TradingView
          </button>
          <button onclick="closeModal()" class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition">
            <i class="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>
      </div>"""

if old_header in content:
  content = content.replace(old_header, new_header)

# 2. Agregar helper para guardar currentModalStrategyId en viewStrategy
old_view_strat = """    async function viewStrategy(id) {
      try {
        const res = await fetch(`/api/strategy/${id}`);
        const data = await res.json();
        document.getElementById('modal-title').innerText = `${id} · Ficha Técnica`;
        document.getElementById('modal-content').innerHTML = marked.parse(data.content);
        document.getElementById('strategy-modal').classList.remove('hidden');"""

new_view_strat = """    async function viewStrategy(id) {
      try {
        window.currentModalStrategyId = id;
        const tvBtn = document.getElementById('modal-tv-btn');
        if (tvBtn) tvBtn.classList.remove('hidden');

        const res = await fetch(`/api/strategy/${id}`);
        const data = await res.json();
        document.getElementById('modal-title').innerText = `${id} · Ficha Técnica`;
        document.getElementById('modal-content').innerHTML = marked.parse(data.content);
        document.getElementById('strategy-modal').classList.remove('hidden');"""

if old_view_strat in content:
  content = content.replace(old_view_strat, new_view_strat)

# 3. Ocultar el botón si se abre un informe general
old_view_rep = """    async function viewReport(filename) {
      try {"""

new_view_rep = """    async function viewReport(filename) {
      try {
        const tvBtn = document.getElementById('modal-tv-btn');
        if (tvBtn) tvBtn.classList.add('hidden');"""

if old_view_rep in content:
  content = content.replace(old_view_rep, new_view_rep)

# 4. Agregar función openCurrentStrategyFromModal
modal_helper = """
    function openCurrentStrategyFromModal() {
      closeModal();
      if (window.currentModalStrategyId) {
        openStrategyInChart(window.currentModalStrategyId);
      }
    }
"""
if 'function openCurrentStrategyFromModal' not in content:
  content = content.replace('function closeModal() {', modal_helper + '\n    function closeModal() {')

tmpl_path.write_text(content, encoding='utf-8')
print("Botón modal de TradingView integrado exitosamente!")
