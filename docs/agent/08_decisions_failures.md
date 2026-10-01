# Decisions / Superseded Paths

Active decisions:
- health and priority are separate models;
- 6d Limiar is third priority;
- temperature/recency/score is not in current MVP;
- manual Bitrix export remains active;
- one Streamlit link with two separate phase panels;
- no combined overview yet;
- user may upload one phase or both;
- `eq_*` and `qual_*` storage is separate;
- native `st.metric` for primary KPIs;
- one daily snapshot per phase/day, same-day rerun replaces;
- executive outside-SLA = 7+;
- preserve stable URLs where possible.
- keep the production Apps Script source versioned at `apps-script/Code.gs`;
- render full phase panels only for a valid base; distinguish no-base state from backend load failure.

Audit handling rule:
- classify each divergence as a code bug, incorrect documentation or product decision before implementation;
- document material product decisions in the same change.

Superseded/not selected:
- Google Cloud Service Account persistence: billing/prepayment friction conflicted with zero-cost MVP.
- Colab + Cloudflare/tunnels: fragile/unfit for stable operation.
- Supabase: unnecessary complexity for current need.
- GitHub Actions solely for file movement: no current value.
- Playwright Bitrix export: prototypes v0.1/v0.2/v0.3 exist, but production keeps manual export.

Static sample caution: fixed dates mean aging/counts change over time; never assert old sample counts without recomputing.

Security caution: admin upload password is not viewer authentication.
