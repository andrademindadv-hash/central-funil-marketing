# Security / Privacy

Never commit:
- shared secrets;
- admin passwords;
- OAuth/API tokens;
- Bitrix credentials;
- real `secrets.toml`;
- real client exports.

Use synthetic fixtures.

Apps Script endpoint is externally reachable and shared-secret protected. This is MVP-grade authorization, not enterprise SSO.

Current Streamlit admin password protects update functionality, not necessarily viewing. Verify viewer access before broad sharing.

Different Google emails are acceptable if the Apps Script executing account explicitly has Sheet access.

Do not log secrets or full sensitive client rows.

This handoff intentionally excludes unrelated client legal/medical/personal data and credentials. It captures operating method, product rules and commercial-system context only.
