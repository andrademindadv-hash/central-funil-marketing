# Data Contracts

Accepted uploads: CSV, XLS, XLSX.
CSV parsing must tolerate semicolon/comma, UTF-8 BOM and Latin-1 fallback.

Required columns:
- ID
- Data da mudança de etapa

Conditional:
- Fase

If `Fase` exists, selected upload must actually contain the expected phase.

ID rules:
- cast to string;
- strip trailing `.0` caused by spreadsheet coercion;
- trim whitespace;
- reject blank IDs;
- reject duplicates (do not silently deduplicate).

Date rules:
- day-first parse;
- reject invalid values;
- timezone reference: `America/Sao_Paulo`;
- aging = today - normalized stage-change date;
- negative aging clips to 0.

Current schema:
`ID`, `data_entrada_fase`, `aging_dias`, `status_saude`, `grupo_fila`, `prioridade_operacional`, `ordem_prioridade`.

History schema:
`data`, `atualizado_em`, `estoque`, `prioridade_hoje`, `backlog`, `dentro_sla`, `atencao`, `limiar`, `fora_sla_7d`, `criticos`, `fora_sla_total`, `pct_fora_sla_total`, `aging_medio`, `aging_mediano`, `aging_max`.

Two-file nuance: both selected files are locally validated before publication starts, but saves are separate network calls. This is **not a fully atomic transaction**: first phase may save and second phase may fail. Do not claim all-or-nothing publication unless a batch backend action is implemented.
