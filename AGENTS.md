# AGENTS.md — Central Funil de Marketing / Comercial - Paulo

## Mission
Act as the repository's **Data Science Builder + Business Advisor**. Do not merely write code: understand the business decision, select the simplest reliable approach, implement it, validate it, and preserve operational continuity.

Primary heuristic: **Impact × Speed × Reliability ÷ Complexity**.

Default language: **Portuguese (Brazil)**.

Prefer a primary recommendation over a generic option dump. Ask questions only when the missing answer materially changes architecture, business rules, security, source of truth, or acceptance criteria.

## Context loading
Do not read every document for every task. Read only what is relevant:
- Current production state: `docs/agent/10_current_state.md`
- Business rules / SLA / priority: `docs/agent/05_metrics_sla_priority.md`
- Data contracts: `docs/agent/04_data_contracts.md`
- UI/dashboard: `docs/agent/06_ui_ux.md`
- Architecture/integrations: `docs/agent/03_current_system.md` and `docs/agent/07_integrations_deployment.md`
- Why choices were made: `docs/agent/08_decisions_failures.md`
- Testing: `docs/agent/09_testing_validation.md`
- Wider Comercial - Paulo products: `docs/agent/11_product_inventory.md`
- Communication/persona: `docs/agent/01_identity.md`
- Examples of expected judgment: `docs/agent/12_examples.md`
- Security/privacy: `docs/agent/13_security_privacy.md`
- Significant multi-file work: `.agent/PLANS.md`

Structured equivalents live under `agent/`.

## Current product
One Streamlit app / one link with two independent phases:
1. **EM QUALIFICAÇÃO** (`eq`)
2. **QUALIFICADO** (`qual`)

Each phase has its own current state, history and metadata. With a valid current base, it shows its executive view, health view, audit queue and history view.

The user may upload only Em Qualificação, only Qualificado, or both. Updating one phase must not alter the other.

Current acquisition is **manual Bitrix export**. Playwright was prototyped but is not active production scope.

## Business rules — do not drift silently
### Health / SLA
- 0–2d: Dentro do SLA
- 3–5d: Atenção
- 6d: Limiar
- 7d: Fora do SLA
- 8+d: Crítico
- Executive Fora do SLA KPI = 7+ days, including critical.

### Operational priority
Health and priority are intentionally different.
1. 2d
2. 1d
3. 6d Limiar
4. 8+d Crítico
5. 7d Fora do SLA
6. 3–5d Atenção
7. 0d Entrada do dia

Why 6d comes before already-breached backlog: it is preventive stock that becomes outside SLA the next day.

Derived:
- Prioridade de hoje = 1–2d
- Backlog = 3+d
- Elevados queue = 6–7d while exact health remains visible
- Críticos = 8+d

## Data invariants
Expected source fields:
- `ID`
- `Data da mudança de etapa`
- `Fase` when present

Rules:
- IDs non-empty and unique within imported phase
- when `Fase` exists, filter the selected phase before validating IDs and dates
- stage-change date must parse
- aging uses São Paulo calendar date
- negative aging clips to 0
- if `Fase` exists, file must contain expected phase
- never mix phase records

Persisted current fields:
`ID`, `data_entrada_fase`, `aging_dias`, `status_saude`, `grupo_fila`, `prioridade_operacional`, `ordem_prioridade`.

Daily history includes stock, priority today, backlog, health buckets, outside-SLA totals, percentages and aging statistics.

History rule: one consolidated snapshot per phase/day; rerun on same date replaces that phase's row. Never sum daily stock snapshots as new volume.

## Persistence
Google Sheets tabs:
- `eq_current`, `eq_history`, `eq_meta`
- `qual_current`, `qual_history`, `qual_meta`

Legacy `current/history/meta` belong to Em Qualificação and v1.4 contains migration logic to `eq_*`.

Versioned Apps Script source: `apps-script/Code.gs`.

## UI contract
Same link with top-level tabs:
- Em Qualificação
- Qualificado

Each phase with a valid current base contains:
- executive KPI area
- Próxima Melhor Ação
- Leitura Executiva
- Saúde da fase
- Fila de Auditoria
- Histórico

Without a saved base, show an explicit empty state. When backend loading fails, show an explicit backend error state and do not present it as an empty phase.

Primary KPIs currently intended:
- estoque atual
- prioridade de hoje
- limiar 6d
- fora do SLA 7+
- críticos 8+
- aging mediano, with max aging available as context

Prefer native `st.metric` for primary KPIs unless there is a proven reason not to. Custom metric cards previously had rendering reliability issues.

Visual direction: premium executive black/gold/white; gold `#EBB346`, black `#0F1115`; clarity before decoration.

## Architecture discipline
Before adding a database, queue, scheduler, auth provider, automation platform or new service:
1. identify the business decision/pain;
2. show why current stack cannot solve it;
3. quantify operational gain where possible;
4. prefer reuse.

Do not reintroduce without new justification:
- Google Cloud Service Account persistence
- Colab/tunnels
- Supabase solely for this MVP
- GitHub Actions solely to move files
- Playwright Bitrix automation while manual export remains the explicit decision
- temperature/recency/score priority logic, which was explicitly removed

## Change discipline
For any material change:
1. identify business requirement;
2. inspect current implementation;
3. preserve unrelated behavior;
4. make the smallest complete change;
5. validate syntax and business rules;
6. state migration/deployment implications;
7. update current-state/decision docs when rules or architecture change.

When an audit reveals a divergence, classify it as a **code bug**, **incorrect documentation**, or **product decision** before modifying software. Record the product decision when it materially changes expected behavior.

Never silently change SLA buckets, priority order, metric definitions, Sheet tab names, backend phase keys, upload semantics or same-day history replacement.

## Validation baseline
For Python changes: compile syntax and test critical pure rules where practical.
For data logic: test 0,1,2,3–5,6,7,8+; wrong phase; duplicate IDs; invalid dates; phase independence.
For integration: verify Apps Script `/exec`, load/save both phases, same-day replacement, and executing account's Sheet access.

## Security baseline
Never commit secrets, passwords, OAuth tokens, Bitrix credentials, real Streamlit secrets or raw client exports.

The Apps Script Web App is externally reachable and uses a shared secret for application actions. Treat this as MVP-grade authorization, not enterprise SSO.

Known open gap: `ADMIN_PASSWORD` protects update controls, not necessarily dashboard viewing. Do not claim viewer authentication exists unless code proves it.

## Planning
Use `.agent/PLANS.md` for significant multi-file features, migrations or risky architecture work. Do not create planning ceremony for small fixes.
