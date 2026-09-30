# Integrations / Deployment

Why Apps Script + Sheets:
- no Google Cloud billing/prepayment requirement for MVP;
- low operational complexity;
- auditable by business users;
- adequate for current daily volume.

Working Apps Script pattern:
- execute as deploying Google account;
- that account must have Sheet edit access;
- endpoint callable by Streamlit;
- `/exec` URL used in Streamlit;
- application actions protected by `CENTRAL_API_SECRET`.

Observed failures:
- `You do not have permission to access the requested document` → executing account lacks Sheet access or wrong spreadsheet target.
- HTTP 401 → Web App restricted to user/owner rather than callable by Streamlit.

Deployment order for backend+frontend changes:
1. update/save `Code.gs`;
2. publish new Web App version;
3. verify `/exec` health;
4. confirm executing account's Sheet access;
5. update GitHub frontend;
6. let Streamlit redeploy;
7. test eq only;
8. test qual only;
9. test both;
10. verify Sheet tabs and same-day history.

Rollback: revert last good GitHub commit and/or prior Apps Script version. Never delete history tabs to roll back.
