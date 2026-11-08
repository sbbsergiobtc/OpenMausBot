# Feed Incremental de Vigilancia Cuantitativa (`@Techain_Trading_Bots`)

> **Pipeline Automatizado ([`sync_new_youtube_videos.py`](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/03_scripts/sync_new_youtube_videos.py)):** Este documento registra de forma automática cualquier vídeo nuevo publicado en el canal `https://www.youtube.com/@Techain_Trading_Bots/videos` (así como nuevas transcripciones recuperadas), clasificando su densidad técnica/cuantitativa (`HIGH_QUANT_VALUE`, `MEDIUM_QUANT_VALUE`, `LOW_OR_PROMOTIONAL`) y mapeando sus reglas a los módulos de `AlgrokQuant` (`jev/`).

---

## Estado Base del Sistema · `2026-11-07 23:46:16 UTC`
- **Vídeos Totales Monitorizados en Catálogo:** `119 / 119` (100% del canal actual indexado en [`catalog.json`](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/00_raw_data/catalog.json)).
- **Metadatos y Descripciones Completas:** `119 / 119` extraídos en [`00_raw_data/metadata_descriptions/`](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/00_raw_data/metadata_descriptions).
- **Transcripciones Completas en Caché:** `36` transcripciones íntegras + recuperación progresiva automática por lotes (`--backfill-batch 5`) en cada ciclo de ejecución.
- **Sincronización Espejo Activa:** Cada nuevo hallazgo cuantitativo se escribe simultáneamente en:
  1. [`techain-quant-lab/01_core_quant_knowledge/06_feed_incremental_nuevos_videos.md`](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/01_core_quant_knowledge/06_feed_incremental_nuevos_videos.md)
  2. [`OpenMausBot/library/quant_foundations/06_feed_incremental_nuevos_videos.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/quant_foundations/06_feed_incremental_nuevos_videos.md)

---
