# Testing / Validation

Business-rule cases:
- aging 0 → Dentro do SLA → priority 7
- aging 1 → Dentro do SLA → priority 2
- aging 2 → Dentro do SLA → priority 1
- aging 4 → Atenção → priority 6
- aging 6 → Limiar → priority 3
- aging 7 → Fora do SLA → priority 5
- aging 9 → Crítico → priority 4

Data integrity tests:
- semicolon CSV
- comma CSV
- UTF-8 BOM
- wrong phase in uploader
- missing ID
- duplicate ID
- missing/invalid date
- future date

Independence:
- updating eq must not mutate qual current/history/meta and vice versa.

History:
- first save of date creates one row;
- second save same date replaces row, does not add another snapshot.

Integration:
- Apps Script health
- load/save eq
- load/save qual
- bad secret rejected
- invalid phase rejected

UI smoke:
- both phase tabs render
- empty states understandable
- admin password exposes upload controls
- one uploader may be empty
- both may be populated
- correct per-phase timestamp
- queue export works
