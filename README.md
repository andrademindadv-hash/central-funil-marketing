# Central Funil de Marketing — v1.5

## O que mudou

A Central agora possui duas fases independentes no mesmo link:

- Em Qualificação
- Qualificado

A importação continua manual.

Na barra lateral, existem dois campos:
- `CSV · Em Qualificação`
- `CSV · Qualificado`

Você pode:
1. selecionar somente Em Qualificação;
2. selecionar somente Qualificado;
3. selecionar os dois e processar em uma única ação.

Atualizar uma fase não altera a outra.

## Regras aplicadas inicialmente às duas fases

### Saúde
- Dentro do SLA: 0–2 dias
- Atenção: 3–5 dias
- Limiar: 6 dias
- Fora do SLA: 7 dias
- Crítico: 8+ dias

### Prioridade operacional
1. 2 dias
2. 1 dia
3. Limiar — 6 dias
4. Crítico — 8+ dias
5. Fora do SLA — 7 dias
6. Atenção — 3–5 dias
7. Entrada do dia — 0 dia

## Google Sheets

O Apps Script cria bases separadas:

- `eq_current`
- `eq_history`
- `eq_meta`
- `qual_current`
- `qual_history`
- `qual_meta`

Se a versão anterior já tiver:
- `current`
- `history`
- `meta`

o Apps Script migra automaticamente esses dados para `eq_*` na primeira leitura de Em Qualificação.

O código-fonte versionado do backend está em [`apps-script/Code.gs`](apps-script/Code.gs).

## Atualização do ambiente existente

1. Substitua `streamlit_app.py` no GitHub.
2. Substitua o conteúdo do editor do Apps Script por `apps-script/Code.gs`.
3. Salve o Apps Script.
4. Crie uma **nova versão da implantação** do Web App.
5. Mantenha a mesma URL `/exec` quando possível.
6. O Streamlit mantém o mesmo link.
