from __future__ import annotations

from datetime import datetime
import re
import unicodedata
from zoneinfo import ZoneInfo

import pandas as pd


TZ = ZoneInfo("America/Sao_Paulo")


def normalize_text(value: object) -> str:
    value = str(value).replace("\ufeff", "").strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).lower()


def find_column(df: pd.DataFrame, *aliases: str) -> str | None:
    mapping = {normalize_text(c): c for c in df.columns}
    for alias in aliases:
        key = normalize_text(alias)
        if key in mapping:
            return mapping[key]
    return None


def health_status(days: int) -> str:
    if days <= 2:
        return "Dentro do SLA"
    if days <= 5:
        return "Atenção"
    if days == 6:
        return "Limiar"
    if days == 7:
        return "Fora do SLA"
    return "Crítico"


def queue_group(days: int) -> str:
    if days <= 2:
        return "Dentro do SLA"
    if days <= 5:
        return "Atenção"
    if days <= 7:
        return "Elevados"
    return "Críticos"


def operational_priority(days: int) -> tuple[int, str]:
    if days == 2:
        return 1, "Prioridade de Hoje · 2 dias"
    if days == 1:
        return 2, "Prioridade de Hoje · 1 dia"
    if days == 6:
        return 3, "Prevenção de SLA · Limiar 6 dias"
    if days >= 8:
        return 4, "Backlog · Crítico"
    if days == 7:
        return 5, "Backlog · Fora do SLA"
    if 3 <= days <= 5:
        return 6, "Backlog · Atenção"
    return 7, "Entrada do dia"


def process_source(df_raw: pd.DataFrame, phase_name: str) -> pd.DataFrame:
    df = df_raw.copy()
    df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]
    df = df.dropna(axis=1, how="all")

    col_id = find_column(df, "ID")
    col_phase = find_column(df, "Fase")
    col_stage_date = find_column(
        df,
        "Data da mudança de etapa",
        "Data da mudanca de etapa",
        "Data da mudança de estágio",
        "Data da mudanca de estagio",
    )

    if col_id is None:
        raise ValueError("Coluna obrigatória 'ID' não encontrada.")
    if col_stage_date is None:
        raise ValueError("Coluna obrigatória 'Data da mudança de etapa' não encontrada.")

    if col_phase is not None:
        phase_norm = df[col_phase].fillna("").map(normalize_text)
        target = normalize_text(phase_name)
        available_phases = sorted(
            {
                str(value).strip()
                for value in df[col_phase].dropna().astype(str)
                if str(value).strip()
            }
        )
        df = df.loc[phase_norm.eq(target)].copy()

        if df.empty:
            found = ", ".join(available_phases[:8]) or "nenhuma fase identificada"
            raise ValueError(
                f"O arquivo selecionado não contém a fase '{phase_name}'. "
                f"Fases encontradas: {found}."
            )

    df[col_id] = (
        df[col_id]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    invalid_ids = df[col_id].isin(["", "nan", "None"])
    if invalid_ids.any():
        raise ValueError(f"{int(invalid_ids.sum())} registro(s) possuem ID vazio.")

    if df[col_id].duplicated().any():
        raise ValueError(
            f"Foram encontrados {int(df[col_id].duplicated().sum())} ID(s) duplicados. "
            "A atualização foi interrompida."
        )

    df["data_entrada_fase"] = pd.to_datetime(
        df[col_stage_date],
        dayfirst=True,
        errors="coerce",
    )

    invalid_dates = df["data_entrada_fase"].isna()
    if invalid_dates.any():
        raise ValueError(
            f"{int(invalid_dates.sum())} registro(s) possuem data de mudança de etapa inválida."
        )

    today = datetime.now(TZ).date()
    df["aging_dias"] = (
        pd.Timestamp(today) - df["data_entrada_fase"].dt.normalize()
    ).dt.days.clip(lower=0).astype(int)

    df["status_saude"] = df["aging_dias"].apply(health_status)
    df["grupo_fila"] = df["aging_dias"].apply(queue_group)

    priority = df["aging_dias"].apply(operational_priority)
    df["ordem_prioridade"] = [item[0] for item in priority]
    df["prioridade_operacional"] = [item[1] for item in priority]

    current = pd.DataFrame(
        {
            "ID": df[col_id].astype(str),
            "data_entrada_fase": df["data_entrada_fase"].dt.strftime("%Y-%m-%d %H:%M:%S"),
            "aging_dias": df["aging_dias"],
            "status_saude": df["status_saude"],
            "grupo_fila": df["grupo_fila"],
            "prioridade_operacional": df["prioridade_operacional"],
            "ordem_prioridade": df["ordem_prioridade"],
        }
    )
    return sort_audit_queue(current).reset_index(drop=True)


def sort_audit_queue(current: pd.DataFrame) -> pd.DataFrame:
    return current.sort_values(
        ["ordem_prioridade", "aging_dias", "data_entrada_fase"],
        ascending=[True, False, True],
    )


def phase_view_state(current: pd.DataFrame, load_error: str | None) -> str:
    if load_error:
        return "backend_error"
    if current.empty:
        return "empty"
    return "ready"


def build_history_row(current: pd.DataFrame, updated_at: datetime) -> pd.DataFrame:
    stock = len(current)
    inside = int((current["aging_dias"] <= 2).sum())
    attention = int(current["aging_dias"].between(3, 5).sum())
    threshold = int((current["aging_dias"] == 6).sum())
    outside_exact = int((current["aging_dias"] == 7).sum())
    critical = int((current["aging_dias"] >= 8).sum())
    outside_total = int((current["aging_dias"] >= 7).sum())
    priority_today = int(current["aging_dias"].isin([1, 2]).sum())
    backlog = int((current["aging_dias"] >= 3).sum())

    return pd.DataFrame(
        [{
            "data": updated_at.date().isoformat(),
            "atualizado_em": updated_at.isoformat(),
            "estoque": stock,
            "prioridade_hoje": priority_today,
            "backlog": backlog,
            "dentro_sla": inside,
            "atencao": attention,
            "limiar": threshold,
            "fora_sla_7d": outside_exact,
            "criticos": critical,
            "fora_sla_total": outside_total,
            "pct_fora_sla_total": outside_total / stock if stock else None,
            "aging_medio": float(current["aging_dias"].mean()) if stock else None,
            "aging_mediano": float(current["aging_dias"].median()) if stock else None,
            "aging_max": int(current["aging_dias"].max()) if stock else None,
        }]
    )
