# Current State — 2026-09-30

Production stack is working:
- GitHub repo `central-funil-marketing`
- Streamlit Community Cloud
- Google Apps Script Web App
- Google Sheets persistence

Most recent generated reference package: **Central Funil — Duas Fases v1.4**.

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
- automated regression tests;
- Bitrix automation only if explicitly reopened.
