# Current System

Architecture:
```text
Bitrix
  ↓ manual CSV/XLS/XLSX by phase
Streamlit Community Cloud
  ↓ Python validation + aging/SLA/priority
Google Apps Script Web App
  ↓
Google Sheets
  ↓
Streamlit reads current/history/meta
```

Primary frontend: `streamlit_app.py`.
Responsibilities: upload UI, parsing, validation, rules, backend calls, executive/health/queue/history rendering.

Primary backend: `apps-script/Code.gs`.
Responsibilities: shared-secret auth, phase config (`eq`/`qual`), `load`, `save`, same-day history replacement, persistence, legacy migration.

Streamlit secrets:
- `APPS_SCRIPT_URL`
- `CENTRAL_API_SECRET`
- `ADMIN_PASSWORD`

Apps Script Properties:
- `CENTRAL_API_SECRET`
- `SPREADSHEET_ID`

The Apps Script must execute as an account that can edit the target Sheet. A prior cross-account permission failure was solved by sharing the Sheet with the executing account.
