# OpenMausBot agent notes

Before claiming a server or conversation change works, follow
[`docs/verification/README.md`](docs/verification/README.md). Always launch an
isolated fixture; never verify mutations against the user's live app or data.

## Comments

Write a comment only for what the code cannot say:

- a license or attribution notice;
- a fact forced by something outside this code (a vendor, CLI, OS, browser,
  Electron or protocol behaviour), with its version when it has one;
- the doc comment of a public contract: the wire types in `shared/`, the
  driver interface, the preload bridge, `config.json` fields people edit;
- a link to an upstream issue;
- a security invariant or a known open risk.

Do not narrate what the next line does, restate a name, record history ("used
to", "no longer", PR or issue numbers, plan or slice names: git has it), point
at other files, draw banners or leave commented-out code. When our own code
needs a paragraph to explain a surprise, change the code instead: a better
name, a type, an extracted function, one shared helper. A rule ("never X",
"must match Y") belongs in a type, a test or a lint rule. Never suppress a lint
rule that guards correctness; fix the code.

More specific `AGENTS.md` files override this note within their directories.

## AlgrokQuant Quantitative Fleet Rules

### Postura Crítica y Rigor Técnico Profesional (Norma Mandatoria)
En todas las interacciones, respuestas, análisis de ideas, preguntas o proposiciones (tanto planteadas por el usuario como generadas internamente por los agentes o el sistema), se debe mantener siempre una **actitud objetivamente crítica y profesional desde el punto de vista técnico como developer de sistemas y como experto en trading cuantitativo-algorítmico**. No aceptar suposiciones sin someterlas a escrutinio matemático, viabilidad computacional, microestructura de mercado, riesgo de sobreajuste y costes de fricción.

### Auto-Deploy Directo a Forward Test (Norma Mandatoria Oficial)
A partir de ahora, cuando se encuentre una estrategia válida que haya pasado por todos los agentes (@StratFinder, @Ideator, @CoderQuant, @Auditor, @Skeptic y @RiskFilter) y sea auditada y aprobada con los filtros de robustez y riesgo (Monte Carlo 1.000 simulaciones, Walk-Forward Analysis, 30% Out-of-Sample ciego, Sharpe ≥ 1.50 y Retorno Anualizado ≥ 30%), **se añadirá DIRECTAMENTE y de forma inmediata a Forward Test en vivo** (cripto o TradFi/índices), asignándosele un libro contable virtual de **$1.000 USD/USDC de balance base inicial**.

### Regla Suprema de Fondeo: Exclusivamente End of Day Drawdown (EOD) - Prohibido Trailing DD
**QUEDA TERMINANTEMENTE PROHIBIDO ASUMIR, MENCIONAR O CALCULAR CONDICIONES DE TRAILING DRAWDOWN.** Sergio **ÚNICAMENTE** trabaja con cuentas que operan bajo **END OF DAY DRAWDOWN (EOD)** calculado al cierre de la sesión diaria.
- Las fluctuaciones intra-trade o beneficios flotantes jamás mueven la marca de agua del drawdown.
- En todas las auditorías, simulaciones de Monte Carlo y filtros de riesgo (@Auditor y @RiskFilter), el drawdown se evalúa **EXCLUSIVAMENTE a fin de día (EOD)**.

### Calibración Dual de Robustez y Drawdown en Auditoría (@Auditor y @RiskFilter)
- **Cuentas de Fondeo (Prop Firms):**
  - **Tipo de Drawdown Obligatorio:** **EXCLUSIVAMENTE END OF DAY (EOD)**. Prohibido Trailing Drawdown.
  - **Tasa de Pase / Intervalo de Confianza Monte Carlo:** Se calibra para exigir un **IC de pase $\ge 70\%$** (3 de cada 4 cuentas simuladas aprueban el challenge). No se exige ni busca un 100% de pase, al ser matemáticamente falaz y provocar sobreajuste letal.
  - **Segmentación por Vehículo Operativo:**
    - **Cuentas de Futuros (CME / Topstep / Apex / Tradovate):** Drawdown máximo estricto de **3.0% a 4.0% END OF DAY (EOD)**.
    - **Cuentas de CFDs / Forex (FTMO, IC Markets Prop, etc.):** Drawdown máximo de **8.0%**.
- **Cuentas de Capital Propio:**
  - Se mantienen **sin cambios** con sus filtros estrictos de preservación de capital: Max Drawdown continuo $\le 20.0\%$, alert DD $-10.0\%$, Sharpe $\ge 1.50$, Retorno Anualizado $\ge 30.0\%$ y probabilidad de ruina del $0.0\%$.


