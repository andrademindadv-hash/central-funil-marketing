# Business Context

The Central exists to answer not only "how many deals exist" but:
- which IDs require action now;
- which stock is approaching SLA rupture;
- how much backlog exists;
- whether the phase is improving;
- when data was last updated.

Core distinction:
- **Health/SLA** = how old the stock is.
- **Operational priority** = order in which the team should act.

The 6-day Limiar is the canonical example: not yet outside SLA, but can be prioritized ahead of breached backlog because tomorrow it breaches if untouched.

Daily snapshots are **state**, not flow.

Wider commercial context previously used these reference targets:
- Base 15 gains/day, Ideal 18, Top 20
- Base week 75, Ideal 90, Top 100
- 22-business-day month references 330 / 396 / 440

Broader "gain" definition: contract + password obtained; stage-change date = day of gain. "Realizar Cadastro" onboarding may count as operational closing in broader reports.

Broader indicators:
- Taxa de Conversão = gains / entries of the day
- Vazão Operacional = gains / qualified by Sofia since last cut

These broader metrics are context, not automatically part of the current phase-aging dashboard.

Known broader funnel stages include Entrada, Qualificação, Remarketing, Qualificados, Handoffs, Pegar Senha, Problemas Senha INSS, Dados para Elaboração Contratual, Onboarding and Negócio Ganho.
