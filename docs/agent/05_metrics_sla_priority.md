# Metrics / SLA / Priority

Health:
- 0–2 Dentro do SLA
- 3–5 Atenção
- 6 Limiar
- 7 Fora do SLA
- 8+ Crítico

Executive Fora do SLA = all aging >= 7, so critical is included.

Prioridade de hoje = aging 1 or 2; order 2d before 1d.
Backlog = aging >= 3.

Operational priority:
1. 2d
2. 1d
3. 6d
4. 8+d
5. 7d
6. 3–5d
7. 0d

Reason for 6d ahead of breached stock: prevent tomorrow's new SLA breach.

Queue filters:
- Críticos: 8+
- Elevados: 6–7
- Atenção: 3–5
- Dentro do SLA: 0–2
- Todos

Elevados is a convenience grouping. Exact status must remain visible.

Current dual-phase executive row:
- Estoque atual
- Prioridade de hoje
- Limiar 6d
- Fora do SLA
- Críticos
- Aging mediano

Aging máximo is contextual/help information.
