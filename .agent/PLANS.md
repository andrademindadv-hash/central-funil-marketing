# Planos de execução

## 2026-09-30 — Correções da auditoria de consistência

Status: implementação concluída e preparada para publicação no GitHub como v1.5; publicação do Apps Script e redeploy do Streamlit permanecem pendentes.

Classificação antes da implementação:
- bug de código: validação de IDs antes do recorte da fase;
- bug de código: filtros da fila ignoram `ordem_prioridade`;
- bug de código: falha do backend é convertida em estado sem base;
- documentação incorreta/incompleta: contrato de UI não condiciona os painéis a uma base válida e o backend versionado não tem caminho explícito;
- decisão de produto: manter empty state simples, mostrar backend error explicitamente e renderizar os painéis completos somente com base válida.

Execução:
1. Versionar o backend em `apps-script/Code.gs`, mantendo fases, abas, migração, `load`, `save` e substituição diária.
2. Extrair regras puras para um módulo testável e corrigir validação, ordenação e estados de carregamento.
3. Integrar as regras no Streamlit sem alterar SLA, prioridade ou semântica de publicação.
4. Adicionar regressões e atualizar documentação de arquitetura, UI, testes, estado e decisões.
5. Validar testes, compilação Python, sintaxe do Apps Script e diff final.
