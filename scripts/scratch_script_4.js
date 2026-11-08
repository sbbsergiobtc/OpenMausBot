
  (function() {
    'use strict';

    class AlgrokTableColumnReorderController {
      constructor() {
        this.storagePrefix = 'algrok_col_order_v3_';
        this.tables = new Map();
        this.activeDrag = null;
        this.ghostEl = null;
        this.indicatorEl = null;
        this.init();
      }

      init() {
        const runScan = () => {
          this.scanAndAttachAll();
        };

        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', runScan);
        } else {
          runScan();
        }

        // Re-escaneos preventivos tras carga asíncrona de módulos
        setTimeout(runScan, 500);
        setTimeout(runScan, 1500);
        setTimeout(runScan, 3000);

        // Eventos globales de arrastre
        window.addEventListener('pointermove', (e) => this.onGlobalPointerMove(e), { passive: false });
        window.addEventListener('pointerup', (e) => this.onGlobalPointerUp(e), { passive: false });
        window.addEventListener('pointercancel', (e) => this.onGlobalPointerUp(e), { passive: false });
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

        // Asignar ID canónico si no lo tiene
        if (!table.id) {
          const tbId = tbody.id ? tbody.id.replace('-tbody', '').replace('-body', '') : '';
          table.id = tbId ? `table-${tbId}` : `table-auto-${fallbackIdx}`;
        }
        const tableId = table.id;

        if (this.tables.has(tableId)) {
          // Ya adjuntado, re-aplicar orden guardado a filas si se añadieron dinámicamente
          const state = this.tables.get(tableId);
          const savedOrder = this.getSavedOrder(tableId);
          if (savedOrder && !this.isDefaultOrder(state.originalKeys, savedOrder)) {
            this.permuteTbodyRows(state, savedOrder);
          }
          return;
        }

        // Asegurar que el contenedor padre soporte la guía de inserción absoluta
        const parentWrapper = table.parentElement;
        if (parentWrapper && getComputedStyle(parentWrapper).position === 'static') {
          parentWrapper.style.position = 'relative';
        }

        // Definir claves originales fijas para cada columna
        const originalKeys = ths.map((th, colIdx) => {
          let key = th.dataset.colKey;
          if (!key) {
            key = `col_${colIdx}`;
            th.dataset.colKey = key;
          }
          th.dataset.origIdx = colIdx.toString();
          th.setAttribute('draggable', 'false');
          th.addEventListener('dragstart', (e) => e.preventDefault());
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

        // Decorar th con grip handle y listener de pointerdown
        ths.forEach((th, colIdx) => {
          th.classList.add('algrok-col-header');
          th.title = 'Arrastra para reordenar columna';
          
          let grip = th.querySelector('.col-drag-grip');
          if (!grip) {
            grip = document.createElement('span');
            grip.className = 'col-drag-grip';
            grip.innerHTML = '<i class="fa-solid fa-grip-vertical"></i>';
            th.insertBefore(grip, th.firstChild);
          }

          th.onpointerdown = (e) => this.onHeaderPointerDown(e, tableId, th);
        });

        // Configurar MutationObserver para sincronizar filas dinámicas (polling)
        const observer = new MutationObserver(() => {
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

        // Inyectar botón de restablecer orden
        this.injectResetControl(table, tableId);

        // Restaurar orden previo si está guardado en localStorage
        const savedOrder = this.getSavedOrder(tableId);
        if (savedOrder && !this.isDefaultOrder(originalKeys, savedOrder) && savedOrder.length === originalKeys.length) {
          this.applyOrderToTable(tableId, savedOrder, false);
        }
      }

      injectResetControl(table, tableId) {
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
        // Ignorar si el clic fue en un botón, enlace o input interno
        if (e.target.closest('button, input, select, a') && !e.target.closest('.col-drag-grip')) {
          return;
        }

        const tableState = this.tables.get(tableId);
        if (!tableState) return;

        const currentThs = Array.from(tableState.headerRow.querySelectorAll('th'));
        const fromIndex = currentThs.indexOf(th);
        if (fromIndex === -1) return;

        // Prevenir selección de texto y native drag
        e.preventDefault();

        // Capturar puntero en el th
        try {
          if (th.setPointerCapture) th.setPointerCapture(e.pointerId);
        } catch (err) {}

        const rect = th.getBoundingClientRect();
        this.activeDrag = {
          pointerId: e.pointerId,
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
        if (!drag.isDragging && dist > 4) {
          drag.isDragging = true;
          document.body.style.cursor = 'grabbing';
          drag.th.classList.add('col-is-dragging');

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
        const labelText = (drag.th.innerText || drag.th.textContent || '').trim().replace(/\s+/g, ' ');
        ghost.innerHTML = `<i class="fa-solid fa-grip-vertical text-[#3C45A5] text-[10px]"></i> <span>${labelText}</span>`;
        ghost.style.width = `${Math.min(drag.width, 240)}px`;
        ghost.style.left = `${e.clientX - drag.offsetX}px`;
        ghost.style.top = `${e.clientY - drag.offsetY}px`;

        document.body.appendChild(ghost);
        this.ghostEl = ghost;

        if (window.Motion && Motion.animate) {
          try {
            Motion.animate(ghost, {
              scale: [0.95, 1.04],
              rotate: [0, 1.2],
              opacity: [0.6, 0.98]
            }, {
              easing: Motion.spring({ stiffness: 450, damping: 25 })
            });
          } catch (err) {}
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

        // Localizar qué encabezado está más cerca del cursor X
        let closestIndex = drag.fromIndex;
        let minDistance = Infinity;

        ths.forEach((targetTh, idx) => {
          const rect = targetTh.getBoundingClientRect();
          const centerX = rect.left + rect.width / 2;
          const dist = Math.abs(e.clientX - centerX);
          if (dist < minDistance) {
            minDistance = dist;
            closestIndex = idx;
          }
        });

        drag.toIndex = closestIndex;
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

        try {
          if (drag.th.releasePointerCapture && drag.pointerId !== undefined) {
            drag.th.releasePointerCapture(drag.pointerId);
          }
        } catch (err) {}

        if (drag.isDragging) {
          drag.th.classList.remove('col-is-dragging');

          // Limpieza inmediata del ghost
          if (this.ghostEl) {
            this.ghostEl.remove();
            this.ghostEl = null;
          }

          if (this.indicatorEl) {
            this.indicatorEl.remove();
            this.indicatorEl = null;
          }

          // Ejecutar reordenamiento si la posición destino es diferente
          if (drag.fromIndex !== drag.toIndex) {
            this.reorderColumn(drag.tableId, drag.fromIndex, drag.toIndex);
          }
        }
      }

      reorderColumn(tableId, fromIdx, toIdx) {
        const tableState = this.tables.get(tableId);
        if (!tableState) return;

        // Obtener el orden actual de claves desde los <th> del DOM
        const currentThs = Array.from(tableState.headerRow.querySelectorAll('th'));
        const currentOrder = currentThs.map(th => th.dataset.colKey);

        const [movedKey] = currentOrder.splice(fromIdx, 1);
        currentOrder.splice(toIdx, 0, movedKey);

        // Aplicar orden al DOM (encabezados y celdas)
        this.applyOrderToTable(tableId, currentOrder, true);
        this.saveOrder(tableId, currentOrder);
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
                setTimeout(() => th.classList.remove('col-reorder-flash'), 750);
                if (window.Motion && Motion.animate) {
                  try {
                    Motion.animate(th, {
                      scale: [0.96, 1.02, 1]
                    }, {
                      easing: Motion.spring({ stiffness: 450, damping: 25 })
                    });
                  } catch (err) {}
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

        rows.forEach(tr => {
          const cells = Array.from(tr.children);
          // Ignorar filas de mensaje vacío o colspan
          if (cells.length !== tableState.originalKeys.length) return;

          // Asignar dataset.colKey a cada celda si no lo tiene (en orden canónico original)
          cells.forEach((td, idx) => {
            if (!td.dataset.colKey) {
              td.dataset.colKey = tableState.originalKeys[idx];
            }
          });

          // Lookup map por clave para garantizar idempotencia total
          const cellMap = new Map();
          cells.forEach(td => cellMap.set(td.dataset.colKey, td));

          const permuted = targetOrder.map(key => cellMap.get(key)).filter(Boolean);
          if (permuted.length === cells.length) {
            tr.replaceChildren(...permuted);
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

    // Inicializar controlador global único
    window.AlgrokTables = new AlgrokTableColumnReorderController();
  })();
  