import os
import re

INDEX_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html = f.read()

print(f"Loaded index.html: {len(html)} bytes")

# 1. Add Motion CDN to <head> if not present
if "cdn.jsdelivr.net/npm/motion@" not in html:
    motion_cdn = """  <!-- Motion (Framer Motion Vanilla Engine) CDN -->
  <script src="https://cdn.jsdelivr.net/npm/motion@11.11.17/dist/motion.js"></script>
"""
    # Insert right after Marked.js
    marked_target = '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>'
    if marked_target in html:
        html = html.replace(marked_target, marked_target + "\n" + motion_cdn, 1)
        print("[OK] Motion CDN inserted after marked.min.js")
    else:
        html = html.replace("</head>", motion_cdn + "\n</head>", 1)
        print("[OK] Motion CDN inserted before </head>")
else:
    print("[INFO] Motion CDN already present")

# 2. Add Table IDs to all 11 tables if not already explicitly assigned
table_mappings = [
    ('portfolio-table-tbody', 'table-portfolio'),
    ('trades-table-body', 'table-trades'),
    ('ft-active-strategies-tbody', 'table-ft-active'),
    ('ft-orders-tbody', 'table-ft-orders'),
    ('ft-trades-table-body', 'table-ft-trades'),
    ('ql-matrix-tbody', 'table-ql-matrix'),
    ('orch-ab-strategies-tbody', 'table-orch-ab'),
    ('tri-facet-table-body', 'table-tri-facet'),
    ('strategies-table-body', 'table-strategies'),
    ('journal-table-body', 'table-journal'),
    ('accounts-table-tbody', 'table-accounts'),
]

for tbody_id, table_id in table_mappings:
    # Look for <table ...> that precedes <tbody id="tbody_id"
    pattern = rf'(<table(?![^>]*id=[\'"][^\'"]+[\'"])([^>]*))(>(?:(?!<table).)*?<tbody[^>]*id=["\']{re.escape(tbody_id)}["\'])'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        old_table_tag = match.group(1)
        new_table_tag = f'<table id="{table_id}"' + match.group(2)
        html = html[:match.start(1)] + new_table_tag + html[match.end(1):]
        print(f"[OK] Added id='{table_id}' to table for tbody '{tbody_id}'")
    else:
        # Check if already has id
        check_pattern = rf'<table[^>]*id=["\']([^"\']+)["\'][^>]*>(?:(?!<table).)*?<tbody[^>]*id=["\']{re.escape(tbody_id)}["\']'
        cm = re.search(check_pattern, html, re.DOTALL)
        if cm:
            print(f"[INFO] Table for tbody '{tbody_id}' already has id='{cm.group(1)}'")
        else:
            print(f"[WARN] Could not find table for tbody '{tbody_id}'")

# 3. Add Drag & Reorder CSS
css_snippet = """
    /* =========================================================================
       ALGROK INSTITUTIONAL - FRAMER MOTION TABLE DRAG & REORDER SYSTEM
       ========================================================================= */
    .algrok-col-header {
      user-select: none !important;
      -webkit-user-select: none !important;
      touch-action: none !important;
      cursor: grab !important;
      position: relative !important;
      transition: background-color 0.2s cubic-bezier(0.16, 1, 0.3, 1), color 0.15s ease !important;
    }
    .algrok-col-header:active {
      cursor: grabbing !important;
    }
    .col-drag-grip {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      height: 14px;
      margin-right: 4px;
      color: #AEAEB2;
      opacity: 0.4;
      cursor: grab;
      transition: opacity 0.15s ease, color 0.15s ease;
      vertical-align: middle;
    }
    .algrok-col-header:hover .col-drag-grip {
      opacity: 1;
      color: #3C45A5;
    }
    .col-is-dragging {
      opacity: 0.32 !important;
      background: rgba(60, 69, 165, 0.08) !important;
      outline: 1.5px dashed #3C45A5 !important;
      outline-offset: -2px !important;
    }
    .col-drag-ghost {
      position: fixed;
      pointer-events: none;
      z-index: 999999;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1.5px solid #3C45A5;
      box-shadow: 0 16px 36px -4px rgba(60, 69, 165, 0.22), 0 6px 16px rgba(0, 0, 0, 0.08);
      border-radius: 8px;
      padding: 7px 14px;
      font-size: 11px;
      font-weight: 700;
      color: #1D1D1F;
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      display: flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
      transform-origin: center center;
      will-change: transform;
    }
    .col-drop-indicator {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 3px;
      background: #3C45A5;
      border-radius: 2px;
      box-shadow: 0 0 10px rgba(60, 69, 165, 0.75);
      pointer-events: none;
      z-index: 60;
      transition: left 0.1s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .col-reorder-flash {
      animation: colFlashAnim 0.75s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes colFlashAnim {
      0% { background-color: rgba(60, 69, 165, 0.24); }
      100% { background-color: transparent; }
    }
    .btn-reset-cols {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      font-family: 'JetBrains Mono', monospace;
      color: #6E6D68;
      background: #F2F2F7;
      border: 1px solid #E5E5EA;
      border-radius: 6px;
      padding: 3px 8px;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .btn-reset-cols:hover {
      background: #E5E5EA;
      color: #181A20;
      border-color: #3C45A5;
    }
"""

if "ALGROK INSTITUTIONAL - FRAMER MOTION TABLE DRAG & REORDER SYSTEM" not in html:
    # Insert in style tag before </style>
    html = html.replace("</style>", css_snippet + "\n  </style>", 1)
    print("[OK] Table Drag CSS styles inserted")
else:
    print("[INFO] Table Drag CSS styles already present")

# 4. Insert AlgrokMotionTableDragEngine JS script before </body>
js_engine = """
  <!-- =========================================================================
       ALGROK UNIVERSAL MOTION TABLE COLUMN DRAG & REORDER ENGINE
       Impulsado por el motor de físicas de muelle (Motion / Framer Motion)
       ========================================================================= -->
  <script>
  (function() {
    'use strict';

    class AlgrokTableColumnReorderController {
      constructor() {
        this.storagePrefix = 'algrok_col_order_v2_';
        this.tables = new Map();
        this.activeDrag = null;
        this.ghostEl = null;
        this.indicatorEl = null;
        this.init();
      }

      init() {
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', () => this.scanAndAttachAll());
        } else {
          this.scanAndAttachAll();
        }

        // Re-escaneo preventivo tras la inicialización de vistas asíncronas
        setTimeout(() => this.scanAndAttachAll(), 800);
        setTimeout(() => this.scanAndAttachAll(), 2500);

        // Limpieza de eventos globales
        window.addEventListener('pointermove', (e) => this.onGlobalPointerMove(e), { passive: false });
        window.addEventListener('pointerup', (e) => this.onGlobalPointerUp(e));
        window.addEventListener('pointercancel', (e) => this.onGlobalPointerUp(e));
      }

      scanAndAttachAll() {
        const allTables = document.querySelectorAll('table');
        allTables.forEach((table, idx) => {
          this.attachToTable(table, idx);
        });
      }

      attachToTable(table, fallbackIdx) {
        if (!table) return;
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');
        if (!thead || !tbody) return;

        const headerRow = thead.querySelector('tr');
        if (!headerRow) return;
        const ths = Array.from(headerRow.querySelectorAll('th'));
        if (ths.length < 2) return;

        // Asignar ID si falta
        if (!table.id) {
          const tbId = tbody.id ? tbody.id.replace('-tbody', '').replace('-body', '') : '';
          table.id = tbId ? `table-${tbId}` : `table-auto-${fallbackIdx}`;
        }

        const tableId = table.id;
        if (this.tables.has(tableId)) {
          // Ya inicializada, verificar si hay nuevas columnas o filas
          return;
        }

        // Asegurar position relative en contenedor para la guía de inserción
        const parentWrapper = table.parentElement;
        if (parentWrapper && getComputedStyle(parentWrapper).position === 'static') {
          parentWrapper.style.position = 'relative';
        }

        // Guardar orden original canónico
        const originalKeys = ths.map((th, colIdx) => {
          const key = th.dataset.colKey || `col_${colIdx}`;
          th.dataset.colKey = key;
          th.dataset.origIdx = colIdx.toString();
          return key;
        });

        const tableState = {
          table,
          thead,
          tbody,
          headerRow,
          originalKeys,
          currentOrder: [...originalKeys],
          isPermuting: false,
          observer: null
        };
        this.tables.set(tableId, tableState);

        // Decorar cada <th> con clase y grip icon
        ths.forEach((th, colIdx) => {
          th.classList.add('algrok-col-header');
          th.title = 'Arrastra para reordenar columna (Framer Motion)';
          
          if (!th.querySelector('.col-drag-grip')) {
            const grip = document.createElement('span');
            grip.className = 'col-drag-grip';
            grip.innerHTML = '<i class="fa-solid fa-grip-vertical"></i>';
            th.insertBefore(grip, th.firstChild);
          }

          th.onpointerdown = (e) => this.onHeaderPointerDown(e, tableId, th);
        });

        // Configurar MutationObserver en tbody para que cada nuevo render por polling se ordene automáticamente
        const observer = new MutationObserver((mutations) => {
          if (tableState.isPermuting) return;
          const savedOrder = this.getSavedOrder(tableId);
          if (!savedOrder || this.isDefaultOrder(originalKeys, savedOrder)) return;

          tableState.isPermuting = true;
          try {
            this.permuteTbodyRows(tableState, savedOrder);
          } finally {
            setTimeout(() => { tableState.isPermuting = false; }, 0);
          }
        });

        observer.observe(tbody, { childList: true });
        tableState.observer = observer;

        // Inyectar botón discreto de reset si no existe
        this.injectResetControl(table, tableId);

        // Restaurar orden desde localStorage si existe
        const savedOrder = this.getSavedOrder(tableId);
        if (savedOrder && !this.isDefaultOrder(originalKeys, savedOrder) && savedOrder.length === originalKeys.length) {
          this.applyOrderToTable(tableId, savedOrder, false);
        }
      }

      injectResetControl(table, tableId) {
        // Buscar un contenedor de cabecera cercano
        const parent = table.closest('.rounded-2xl, .overflow-hidden, .card') || table.parentElement;
        if (!parent) return;
        
        let resetBtn = parent.querySelector(`.btn-reset-cols[data-for="${tableId}"]`);
        if (!resetBtn) {
          resetBtn = document.createElement('button');
          resetBtn.className = 'btn-reset-cols hidden';
          resetBtn.dataset.for = tableId;
          resetBtn.innerHTML = '<i class="fa-solid fa-arrow-rotate-left"></i> Restablecer Columnas';
          resetBtn.title = 'Volver al orden de columnas predeterminado';
          resetBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.resetTableOrder(tableId);
          };

          // Intentar insertar cerca del título o filtros
          const headingArea = parent.querySelector('h2, h3, .flex.items-center.justify-between, .flex.items-center.gap-2');
          if (headingArea) {
            headingArea.appendChild(resetBtn);
          } else {
            table.parentElement.insertBefore(resetBtn, table);
          }
        }
      }

      updateResetButtonVisibility(tableId) {
        const tableState = this.tables.get(tableId);
        if (!tableState) return;
        const parent = tableState.table.closest('.rounded-2xl, .overflow-hidden, .card') || tableState.table.parentElement;
        if (!parent) return;
        const resetBtn = parent.querySelector(`.btn-reset-cols[data-for="${tableId}"]`);
        if (!resetBtn) return;

        const isDefault = this.isDefaultOrder(tableState.originalKeys, tableState.currentOrder);
        if (isDefault) {
          resetBtn.classList.add('hidden');
        } else {
          resetBtn.classList.remove('hidden');
        }
      }

      onHeaderPointerDown(e, tableId, th) {
        // Ignorar si se hace clic en inputs, botones o links dentro del th
        if (e.target.closest('button, input, select, a') && !e.target.closest('.col-drag-grip')) {
          return;
        }

        const tableState = this.tables.get(tableId);
        if (!tableState) return;

        const currentThs = Array.from(tableState.headerRow.querySelectorAll('th'));
        const fromIndex = currentThs.indexOf(th);
        if (fromIndex === -1) return;

        const rect = th.getBoundingClientRect();
        this.activeDrag = {
          tableId,
          tableState,
          th,
          fromIndex,
          toIndex: fromIndex,
          startX: e.clientX,
          startY: e.clientY,
          offsetX: e.clientX - rect.left,
          offsetY: e.clientY - rect.top,
          width: rect.width,
          height: rect.height,
          isDragging: false
        };
      }

      onGlobalPointerMove(e) {
        if (!this.activeDrag) return;
        const drag = this.activeDrag;

        const dist = Math.hypot(e.clientX - drag.startX, e.clientY - drag.startY);
        if (!drag.isDragging && dist > 5) {
          // Iniciar arrastre real
          drag.isDragging = true;
          document.body.style.cursor = 'grabbing';
          drag.th.classList.add('col-is-dragging');

          // Crear Ghost pill con diseño Framer Motion
          this.createGhost(drag, e);
          this.createDropIndicator(drag);
        }

        if (drag.isDragging) {
          e.preventDefault();
          this.updateGhostPosition(e);
          this.updateDropTarget(e);
        }
      }

      createGhost(drag, e) {
        if (this.ghostEl) this.ghostEl.remove();

        const ghost = document.createElement('div');
        ghost.className = 'col-drag-ghost';
        // Obtener texto limpio
        const textContent = drag.th.textContent.replace(/[\\r\\n]+/g, ' ').trim();
        ghost.innerHTML = `<i class="fa-solid fa-grip-vertical text-[#3C45A5] text-[10px]"></i> <span>${textContent}</span>`;
        ghost.style.width = `${Math.min(drag.width, 220)}px`;
        ghost.style.left = `${e.clientX - drag.offsetX}px`;
        ghost.style.top = `${e.clientY - drag.offsetY}px`;

        document.body.appendChild(ghost);
        this.ghostEl = ghost;

        // Animación suave de entrada con Motion si está disponible
        if (window.Motion && Motion.animate) {
          Motion.animate(ghost, {
            scale: [0.94, 1.04],
            rotate: [0, 1.5],
            opacity: [0.6, 0.98]
          }, {
            easing: Motion.spring({ stiffness: 450, damping: 25 })
          });
        }
      }

      createDropIndicator(drag) {
        if (this.indicatorEl) this.indicatorEl.remove();

        const indicator = document.createElement('div');
        indicator.className = 'col-drop-indicator';
        
        const wrapper = drag.tableState.table.parentElement;
        wrapper.appendChild(indicator);
        this.indicatorEl = indicator;
        this.updateIndicatorPosition(drag.fromIndex);
      }

      updateGhostPosition(e) {
        if (!this.ghostEl || !this.activeDrag) return;
        const drag = this.activeDrag;
        const x = e.clientX - drag.offsetX;
        const y = e.clientY - drag.offsetY;

        this.ghostEl.style.left = `${x}px`;
        this.ghostEl.style.top = `${y}px`;
      }

      updateDropTarget(e) {
        if (!this.activeDrag) return;
        const drag = this.activeDrag;
        const ths = Array.from(drag.tableState.headerRow.querySelectorAll('th'));

        let closestIndex = drag.fromIndex;
        let minDistance = Infinity;

        ths.forEach((th, idx) => {
          const rect = th.getBoundingClientRect();
          const centerX = rect.left + rect.width / 2;
          const dist = Math.abs(e.clientX - centerX);
          if (dist < minDistance) {
            minDistance = dist;
            closestIndex = (e.clientX > centerX && idx < ths.length - 1) ? idx + 1 : idx;
          }
        });

        drag.toIndex = Math.max(0, Math.min(ths.length - 1, closestIndex));
        this.updateIndicatorPosition(drag.toIndex);
      }

      updateIndicatorPosition(targetIdx) {
        if (!this.indicatorEl || !this.activeDrag) return;
        const drag = this.activeDrag;
        const ths = Array.from(drag.tableState.headerRow.querySelectorAll('th'));
        const targetTh = ths[targetIdx];
        if (!targetTh) return;

        const tableRect = drag.tableState.table.getBoundingClientRect();
        const thRect = targetTh.getBoundingClientRect();
        const wrapperRect = drag.tableState.table.parentElement.getBoundingClientRect();

        let leftPos = thRect.left - wrapperRect.left;
        if (targetIdx > drag.fromIndex) {
          leftPos = (thRect.right - wrapperRect.left) - 2;
        }

        this.indicatorEl.style.left = `${leftPos}px`;
        this.indicatorEl.style.top = `0px`;
        this.indicatorEl.style.height = `${tableRect.height}px`;
      }

      onGlobalPointerUp(e) {
        if (!this.activeDrag) return;
        const drag = this.activeDrag;
        this.activeDrag = null;
        document.body.style.cursor = '';

        if (drag.isDragging) {
          drag.th.classList.remove('col-is-dragging');

          if (this.ghostEl) {
            // Animación de disolución con físicas spring
            if (window.Motion && Motion.animate) {
              Motion.animate(this.ghostEl, {
                scale: 0.9,
                opacity: 0
              }, {
                duration: 0.18,
                easing: 'ease-out'
              }).finished.then(() => {
                if (this.ghostEl) this.ghostEl.remove();
                this.ghostEl = null;
              });
            } else {
              this.ghostEl.remove();
              this.ghostEl = null;
            }
          }

          if (this.indicatorEl) {
            this.indicatorEl.remove();
            this.indicatorEl = null;
          }

          // Ejecutar intercambio si cambió de posición
          if (drag.fromIndex !== drag.toIndex) {
            this.reorderColumn(drag.tableId, drag.fromIndex, drag.toIndex);
          }
        }
      }

      reorderColumn(tableId, fromIdx, toIdx) {
        const tableState = this.tables.get(tableId);
        if (!tableState) return;

        const ths = Array.from(tableState.headerRow.querySelectorAll('th'));
        const movedTh = ths[fromIdx];
        if (!movedTh) return;

        // Calcular nuevo arreglo de orden
        const newOrder = [...tableState.currentOrder];
        const [removedKey] = newOrder.splice(fromIdx, 1);
        newOrder.splice(toIdx, 0, removedKey);

        // Aplicar orden al DOM y persistir
        this.applyOrderToTable(tableId, newOrder, true);
        this.saveOrder(tableId, newOrder);
        this.updateResetButtonVisibility(tableId);
      }

      applyOrderToTable(tableId, newOrder, triggerAnimation = false) {
        const tableState = this.tables.get(tableId);
        if (!tableState) return;

        tableState.isPermuting = true;
        try {
          // 1. Reordenar encabezados (<th>)
          const thMap = new Map();
          Array.from(tableState.headerRow.querySelectorAll('th')).forEach(th => {
            thMap.set(th.dataset.colKey, th);
          });

          newOrder.forEach(key => {
            const th = thMap.get(key);
            if (th) {
              tableState.headerRow.appendChild(th);
              if (triggerAnimation) {
                th.classList.add('col-reorder-flash');
                setTimeout(() => th.classList.remove('col-reorder-flash'), 800);
                if (window.Motion && Motion.animate) {
                  Motion.animate(th, {
                    scale: [0.96, 1.02, 1]
                  }, {
                    easing: Motion.spring({ stiffness: 400, damping: 26 })
                  });
                }
              }
            }
          });

          // 2. Reordenar celdas de las filas en tbody
          this.permuteTbodyRows(tableState, newOrder);
          tableState.currentOrder = [...newOrder];
        } finally {
          setTimeout(() => { tableState.isPermuting = false; }, 0);
        }
      }

      permuteTbodyRows(tableState, targetOrder) {
        const rows = tableState.tbody.querySelectorAll('tr');
        if (!rows.length) return;

        // Crear mapa de posiciones: para cada posición en targetOrder, qué índice original le corresponde
        const keyToIndex = new Map();
        tableState.originalKeys.forEach((key, idx) => keyToIndex.set(key, idx));
        const indexMapping = targetOrder.map(key => keyToIndex.get(key));

        rows.forEach(tr => {
          const cells = Array.from(tr.children);
          // Si la fila tiene colspan (ej. "No hay operaciones registradas") o no coincide en columnas, ignorar
          if (cells.length !== tableState.originalKeys.length) return;

          // Reordenar las celdas
          const permutedCells = indexMapping.map(origIdx => cells[origIdx]).filter(Boolean);
          if (permutedCells.length === cells.length) {
            tr.replaceChildren(...permutedCells);
          }
        });
      }

      resetTableOrder(tableId) {
        const tableState = this.tables.get(tableId);
        if (!tableState) return;

        this.applyOrderToTable(tableId, tableState.originalKeys, true);
        localStorage.removeItem(this.storagePrefix + tableId);
        this.updateResetButtonVisibility(tableId);
      }

      getSavedOrder(tableId) {
        try {
          const raw = localStorage.getItem(this.storagePrefix + tableId);
          return raw ? JSON.parse(raw) : null;
        } catch (e) {
          return null;
        }
      }

      saveOrder(tableId, order) {
        try {
          localStorage.setItem(this.storagePrefix + tableId, JSON.stringify(order));
        } catch (e) {
          console.warn('Error saving table order:', e);
        }
      }

      isDefaultOrder(orig, curr) {
        if (!curr || orig.length !== curr.length) return true;
        return orig.every((key, i) => key === curr[i]);
      }
    }

    // Inicializar singleton y exponer globalmente para acceso manual
    window.AlgrokTables = new AlgrokTableColumnReorderController();
  })();
  </script>
"""

if "ALGROK UNIVERSAL MOTION TABLE COLUMN DRAG & REORDER ENGINE" not in html:
    html = html.replace("</body>", js_engine + "\n</body>", 1)
    print("[OK] AlgrokMotionTableDragEngine JS script inserted before </body>")
else:
    print("[INFO] AlgrokMotionTableDragEngine already present")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("[SUCCESS] index.html updated successfully!")
