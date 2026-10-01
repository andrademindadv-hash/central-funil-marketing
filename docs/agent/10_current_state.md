# Current State — 2026-10-01

Production stack is working:
- GitHub repo `central-funil-marketing`
- Streamlit Community Cloud
- Google Apps Script Web App
- Google Sheets persistence

The Apps Script source is versioned at `apps-script/Code.gs`. The existing production Web App requires a new version deployment before these backend changes become live.

Most recent repository release: **Central Funil — Duas Fases v1.5**.

Current phases:
- Em Qualificação
- Qualificado

Current import: manual Bitrix export; Streamlit supports one phase or both.

Current SLA:
0–2 / 3–5 / 6 / 7 / 8+ as documented.

Current priority:
2d → 1d → 6d → 8+d → 7d → 3–5d → 0d.

Expected tabs:
- eq_current / eq_history / eq_meta
- qual_current / qual_history / qual_meta

Upload validation scopes IDs and dates to the selected phase. Audit queues always sort by operational priority first. The UI distinguishes a phase with no saved base from a backend loading failure.

The user successfully resolved the Streamlit ↔ Apps Script ↔ Google Sheets connection, including cross-account Sheet permission.

Immediate validation focus:
- real Bitrix CSV counts;
- aging;
- health buckets;
- priority order;
- phase independence;
- history behavior.

Open hardening:
- viewer authentication/privacy;
- true atomic two-phase publish if required;
- evergreen fixtures;
- Bitrix automation only if explicitly reopened.
