---
name: Algrokquant Design System
description: Institutional Quantitative Trading Desk & Telemetry Dashboard
colors:
  canvas: "#F5EFE6"
  sidebar: "#EFECE6"
  surface: "#FDFDFB"
  card: "#FFFFFF"
  muted: "#EAE5DC"
  primary: "#181A20"
  brand: "#5865F2"
  warning: "#C86D3B"
  borderWarm: "#E6E2D8"
  borderDashed: "#B5B2A8"
  txtPrimary: "#181A20"
  txtSecondary: "#6E6D68"
  txtMuted: "#9E9C94"
  profit: "#10B981"
  loss: "#EF4444"
typography:
  headline:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
  mono-data:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.875rem"
    fontWeight: 500
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
---

# Algrokquant Design System

<!-- impeccable:design-schema 1 -->

## Overview
ALGROK QUANT es un panel de trading cuantitativo institucional enfocado a la observabilidad operativa y control de riesgos de bots. La interfaz combina la calidez editorial contemporánea (tema claro arena/cálido) con la máxima precisión técnica de terminales cuantitativas.

## Colors
- **Fondos:**
  - `canvas` (`#F5EFE6`): Fondo base de la aplicación.
  - `sidebar` (`#EFECE6`): Panel lateral de navegación.
  - `surface` (`#FDFDFB`) / `card` (`#FFFFFF`): Contenedores de métricas y gráficos.
- **Textos:**
  - `txtPrimary` (`#181A20`): Texto principal, cifras clave y encabezados.
  - `txtSecondary` (`#6E6D68`): Etiquetas secundarias y descripciones.
  - `txtMuted` (`#9E9C94`): Metadatos y marcas temporales (debe vigilarse contraste mínimo 4.5:1).
- **Semántica Financiera:**
  - `profit` (`#10B981`): Rendimiento positivo, trades ganadores.
  - `loss` (`#EF4444`): Drawdown, pérdidas, alertas críticas.
  - `warning` (`#C86D3B`): Advertencias de latencia o riesgo intermedio.

## Typography
- **Plus Jakarta Sans:** Usada para títulos, navegación y textos narrativos.
- **JetBrains Mono:** Mandatoria para toda cifra numérica, precios, PnL, lotajes, Sharpe ratio y timestamps, con ancho tabular para evitar saltos de línea al actualizar datos en vivo.

## Layout
- Arquitectura de panel con Sidebar colapsable a la izquierda y viewport de dashboards con cuadrícula modular de tarjetas métricas (KPIs superiores, gráficos interactivos centrales y tablas de órdenes en sección inferior).

## Elevation & Depth
- Bordes nítidos (`#E6E2D8`) con sombras mínimas (`shadow-sm`) para priorizar la nitidez sobre el volumen artificial.

## Shapes
- Radios de borde controlados: `rounded-md` (8px) para tarjetas y `rounded-sm` (4px) para píldoras de estado y badges.

## Components
- **Tarjetas de Telemetría:** Fondo blanco/superficie con borde sutil, título secundario en la parte superior y métrica principal monoespaciada en grande.
- **Gráficos Financieros:** Renderizados vía ApexCharts y TradingView embeds sobre fondo limpio.

## Do's and Don'ts
- **DO:** Usar `JetBrains Mono` con alineación derecha en todas las columnas de números en tablas.
- **DO:** Mantener ratios de contraste WCAG AA (≥ 4.5:1) especialmente sobre fondos cálidos/arena.
- **DON'T:** Usar textos en tamaño menor a 11px en etiquetas de telemetría.
- **DON'T:** Añadir gradientes púrpuras o animaciones lentas que entorpezcan la lectura de datos en vivo.
