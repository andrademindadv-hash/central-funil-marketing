from __future__ import annotations

from io import BytesIO
from datetime import datetime
from pathlib import Path
import json
import re
import unicodedata
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Central · Funil de Marketing",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

TZ = ZoneInfo("America/Sao_Paulo")

PHASES = {
    "eq": {
        "name": "EM QUALIFICAÇÃO",
        "label": "Em Qualificação",
        "subtitle": "Proteja a janela operacional, controle o backlog e atue nos IDs certos.",
    },
    "qual": {
        "name": "QUALIFICADO",
        "label": "Qualificado",
        "subtitle": "Acompanhe a permanência na fase, previna ruptura de SLA e priorize a atuação.",
    },
}

HEALTH_ORDER = [
    "Dentro do SLA",
    "Atenção",
    "Limiar",
    "Fora do SLA",
    "Crítico",
]

HEALTH_COLORS = {
    "Dentro do SLA": "#22A06B",
    "Atenção": "#E7A93A",
    "Limiar": "#E38B2C",
    "Fora do SLA": "#D66B2C",
    "Crítico": "#D64545",
}


# ============================================================
# UI
# ============================================================

st.markdown(
    """
<style>
:root {
    --aa-gold: #EBB346;
    --aa-black: #0F1115;
    --aa-panel: #FFFFFF;
    --aa-bg: #F4F5F7;
}
.stApp {
    background:
        radial-gradient(circle at 88% -8%, rgba(235,179,70,.10), transparent 25%),
        var(--aa-bg);
}
.block-container {
    max-width: 1540px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
}
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E3E6EA;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 5px 18px rgba(15,17,21,.04);
}
[data-testid="stMetricLabel"] { font-weight: 700; }
[data-testid="stMetricValue"] {
    font-weight: 850;
    letter-spacing: -0.03em;
}
[data-testid="stDataFrame"] {
    border: 1px solid #E2E5E9;
    border-radius: 14px;
    overflow: hidden;
}
div[data-testid="stSidebar"] {
    border-right: 1px solid #E1E4E8;
}
.aa-kicker {
    color: #9B7A35;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-size: .72rem;
    font-weight: 800;
    margin-bottom: .2rem;
}
.aa-title {
    font-size: 2.15rem;
    line-height: 1.04;
    font-weight: 900;
    letter-spacing: -.04em;
    color: #121419;
    margin-bottom: .35rem;
}
.aa-subtitle {
    color: #717782;
    font-size: .95rem;
    margin-bottom: 1.1rem;
}
.aa-phase-title {
    font-size: 1.7rem;
    line-height: 1.06;
    font-weight: 900;
    letter-spacing: -.035em;
    color: #15171B;
    margin: .8rem 0 .25rem 0;
}
.aa-refresh {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    background: #111318;
    color: #F5D89A;
    border-radius: 999px;
    padding: .45rem .72rem;
    font-size: .76rem;
    font-weight: 750;
    margin-bottom: 1rem;
}
.aa-section-kicker {
    color: #9298A2;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-size: .68rem;
    font-weight: 800;
    margin-top: .35rem;
}
.aa-section-title {
    font-size: 1.42rem;
    line-height: 1.15;
    font-weight: 850;
    letter-spacing: -.025em;
    color: #17191E;
    margin: .15rem 0 .25rem 0;
}
.aa-section-copy {
    color: #747A85;
    font-size: .88rem;
    margin-bottom: 1rem;
}
.aa-insight {
    background: white;
    border: 1px solid #E1E4E8;
    border-left: 4px solid #EBB346;
    border-radius: 15px;
    padding: 1rem 1.05rem;
    min-height: 150px;
}
.aa-insight strong { color: #16191F; }
.aa-action {
    background: linear-gradient(135deg,#101217,#1A1D23);
    border-radius: 15px;
    padding: 1rem 1.05rem;
    min-height: 150px;
    color: white;
}
.aa-action-kicker {
    color: #EBB346;
    font-size: .7rem;
    letter-spacing: .13em;
    font-weight: 850;
    text-transform: uppercase;
}
.aa-action-number {
    color: #EBB346;
    font-size: 2.5rem;
    font-weight: 900;
    line-height: 1;
    margin: .55rem 0 .35rem 0;
}
.aa-action-copy {
    color: #C4C8CF;
    font-size: .83rem;
    line-height: 1.45;
}
.small-muted {
    color: #838995;
    font-size: .78rem;
}
.upload-card {
    background: #FFFFFF;
    border: 1px solid #E3E6EA;
    border-radius: 14px;
    padding: .65rem .8rem;
    margin-bottom: .5rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# UTILITÁRIOS
# ============================================================

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


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    raw = uploaded_file.getvalue()
    buffer = BytesIO(raw)

    if suffix == ".xls":
        return pd.read_excel(buffer, engine="xlrd")
    if suffix == ".xlsx":
        return pd.read_excel(buffer, engine="openpyxl")
    if suffix != ".csv":
        raise ValueError("Formato não suportado. Utilize CSV, XLS ou XLSX.")

    attempts = [
        {"sep": None, "engine": "python", "encoding": "utf-8-sig"},
        {"sep": ";", "encoding": "utf-8-sig"},
        {"sep": ",", "encoding": "utf-8-sig"},
        {"sep": None, "engine": "python", "encoding": "latin1"},
    ]
    last_error = None
    for kwargs in attempts:
        try:
            buffer.seek(0)
            temp = pd.read_csv(buffer, **kwargs)
            if temp.shape[1] >= 2:
                return temp
        except Exception as exc:
            last_error = exc

    raise ValueError(f"Não foi possível interpretar o CSV. Último erro: {last_error}")


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
    # Mesma regra para as duas fases nesta versão:
    # 1º 2 dias
    # 2º 1 dia
    # 3º Limiar 6 dias
    # 4º Crítico 8+ dias
    # 5º Fora do SLA 7 dias
    # 6º Atenção 3–5 dias
    # 7º Entrada do dia 0 dia
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

    if col_phase is not None:
        phase_norm = df[col_phase].fillna("").map(normalize_text)
        target = normalize_text(phase_name)

        available_phases = sorted(
            {
                str(v).strip()
                for v in df[col_phase].dropna().astype(str)
                if str(v).strip()
            }
        )

        df = df.loc[phase_norm.eq(target)].copy()

        if df.empty:
            found = ", ".join(available_phases[:8]) or "nenhuma fase identificada"
            raise ValueError(
                f"O arquivo selecionado não contém a fase '{phase_name}'. "
                f"Fases encontradas: {found}."
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

    return current.sort_values(
        ["ordem_prioridade", "aging_dias", "data_entrada_fase"],
        ascending=[True, False, True],
    ).reset_index(drop=True)


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


def df_records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", date_format="iso"))


# ============================================================
# APPS SCRIPT — PERSISTÊNCIA GRATUITA
# ============================================================

def backend_request(action: str, **payload):
    try:
        api_url = st.secrets["APPS_SCRIPT_URL"]
        api_secret = st.secrets["CENTRAL_API_SECRET"]
    except Exception as exc:
        raise RuntimeError(
            "Configure APPS_SCRIPT_URL e CENTRAL_API_SECRET nos Secrets do Streamlit."
        ) from exc

    body = {
        "action": action,
        "secret": api_secret,
        **payload,
    }

    response = requests.post(
        api_url,
        json=body,
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()

    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError(
            "O Apps Script respondeu em formato inesperado. "
            "Confirme se foi implantado como Web App usando a URL /exec."
        ) from exc

    if not data.get("ok"):
        raise RuntimeError(data.get("error", "Erro não identificado no Apps Script."))

    return data


def normalize_loaded_data(current: pd.DataFrame, history: pd.DataFrame):
    if not current.empty:
        current["aging_dias"] = pd.to_numeric(current["aging_dias"], errors="coerce")
        current["ordem_prioridade"] = pd.to_numeric(
            current["ordem_prioridade"], errors="coerce"
        )

    if not history.empty:
        numeric_cols = [
            "estoque", "prioridade_hoje", "backlog", "dentro_sla",
            "atencao", "limiar", "fora_sla_7d", "criticos",
            "fora_sla_total", "pct_fora_sla_total", "aging_medio",
            "aging_mediano", "aging_max",
        ]
        for col in numeric_cols:
            if col in history.columns:
                history[col] = pd.to_numeric(history[col], errors="coerce")

        if "data" in history.columns:
            history["data"] = pd.to_datetime(history["data"], errors="coerce")

    return current, history


def load_phase_data(phase_key: str):
    data = backend_request("load", phase=phase_key)

    current = pd.DataFrame(data.get("current", []))
    history = pd.DataFrame(data.get("history", []))
    meta = data.get("meta", {}) or {}

    current, history = normalize_loaded_data(current, history)
    return current, history, meta


def persist_update(
    phase_key: str,
    phase_name: str,
    current: pd.DataFrame,
    history_row: pd.DataFrame,
    source_file: str,
):
    now = datetime.now(TZ)

    meta = {
        "status": "SUCESSO",
        "ultima_atualizacao": now.isoformat(),
        "arquivo_origem": source_file,
        "negocios_processados": str(len(current)),
        "fase": phase_name,
        "versao_regras": "SLA-2026-09-v2",
    }

    backend_request(
        "save",
        phase=phase_key,
        current=df_records(current),
        history_row=df_records(history_row)[0],
        meta=meta,
    )


# ============================================================
# SIDEBAR — IMPORTAÇÃO MANUAL DAS DUAS FASES
# ============================================================

with st.sidebar:
    st.markdown("## ⚡ Central de Auditoria")
    st.caption("Funil de Marketing · Produção gratuita")
    st.divider()

    st.markdown("### Atualizar dados")
    st.caption(
        "Você pode importar somente uma fase ou as duas no mesmo processamento."
    )

    admin_password = st.text_input(
        "Senha de atualização",
        type="password",
        key="admin_password",
    )
    expected_password = st.secrets.get("ADMIN_PASSWORD", "")

    if expected_password and admin_password == expected_password:
        uploaded_eq = st.file_uploader(
            "CSV · Em Qualificação",
            type=["csv", "xls", "xlsx"],
            key="upload_eq",
            help="Selecione o arquivo exportado da fase EM QUALIFICAÇÃO.",
        )

        uploaded_qual = st.file_uploader(
            "CSV · Qualificado",
            type=["csv", "xls", "xlsx"],
            key="upload_qual",
            help="Selecione o arquivo exportado da fase QUALIFICADO.",
        )

        selected_count = int(uploaded_eq is not None) + int(uploaded_qual is not None)

        if selected_count == 0:
            st.caption("Nenhum arquivo selecionado.")
        elif selected_count == 1:
            st.caption("1 fase selecionada para atualização.")
        else:
            st.caption("2 fases selecionadas para atualização conjunta.")

        if st.button(
            "Processar e publicar",
            type="primary",
            use_container_width=True,
            disabled=selected_count == 0,
        ):
            selected = []
            if uploaded_eq is not None:
                selected.append(("eq", PHASES["eq"], uploaded_eq))
            if uploaded_qual is not None:
                selected.append(("qual", PHASES["qual"], uploaded_qual))

            prepared = []

            # Primeiro valida/processa tudo. Se um dos arquivos estiver errado,
            # nenhum dos dois é publicado.
            try:
                for phase_key, config, uploaded in selected:
                    source = read_uploaded_file(uploaded)
                    current_new = process_source(source, config["name"])
                    update_time = datetime.now(TZ)
                    history_row = build_history_row(current_new, update_time)

                    prepared.append(
                        {
                            "phase_key": phase_key,
                            "config": config,
                            "uploaded": uploaded,
                            "current": current_new,
                            "history_row": history_row,
                        }
                    )

                # Publicação só começa após todos os arquivos selecionados
                # passarem pela validação local.
                results = []
                for item in prepared:
                    persist_update(
                        phase_key=item["phase_key"],
                        phase_name=item["config"]["name"],
                        current=item["current"],
                        history_row=item["history_row"],
                        source_file=item["uploaded"].name,
                    )
                    results.append(
                        f"{item['config']['label']}: {len(item['current'])} negócios"
                    )

                st.cache_data.clear()
                st.success("Atualização concluída · " + " · ".join(results))
                st.rerun()

            except Exception as exc:
                st.error(f"Atualização interrompida: {exc}")

    elif admin_password:
        st.error("Senha de atualização inválida.")

    st.divider()
    st.caption(
        "Cada fase possui sua própria base e histórico. "
        "Atualizar uma fase não altera a outra."
    )


# ============================================================
# CARREGAMENTO DAS DUAS FASES
# ============================================================

@st.cache_data(ttl=60)
def cached_load_phase(phase_key: str):
    return load_phase_data(phase_key)


phase_data = {}

for phase_key in PHASES:
    try:
        phase_data[phase_key] = cached_load_phase(phase_key)
    except Exception as exc:
        phase_data[phase_key] = (pd.DataFrame(), pd.DataFrame(), {})
        st.warning(
            f"Não foi possível carregar {PHASES[phase_key]['label']}: {exc}"
        )


# ============================================================
# RENDERIZAÇÃO
# ============================================================

def format_last_update(meta: dict) -> str:
    value = meta.get("ultima_atualizacao")
    if not value:
        return "Nenhuma atualização concluída"

    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.astimezone(TZ).strftime("%d/%m/%Y · %H:%M:%S")
    except Exception:
        return str(value)


def render_phase_dashboard(
    phase_key: str,
    config: dict,
    current: pd.DataFrame,
    history: pd.DataFrame,
    meta: dict,
):
    st.markdown(
        f'<div class="aa-phase-title">{config["label"]} · Command Center</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="aa-subtitle">{config["subtitle"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="aa-refresh">● ÚLTIMA ATUALIZAÇÃO&nbsp;&nbsp;{format_last_update(meta)}</div>',
        unsafe_allow_html=True,
    )

    if current.empty:
        st.info(
            f"O painel de {config['label']} ainda não possui base processada. "
            "Use a barra lateral para importar o primeiro CSV desta fase."
        )
        return

    stock = len(current)
    priority_today = int(current["aging_dias"].isin([1, 2]).sum())
    threshold = int((current["aging_dias"] == 6).sum())
    backlog = int((current["aging_dias"] >= 3).sum())
    outside_sla = int((current["aging_dias"] >= 7).sum())
    critical = int((current["aging_dias"] >= 8).sum())
    median_age = float(current["aging_dias"].median())
    max_age = int(current["aging_dias"].max())

    st.markdown(
        '<div class="aa-section-kicker">VISÃO EXECUTIVA</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="aa-section-title">O que exige atenção agora?</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="aa-section-copy">'
        'A janela de 1–2 dias vem primeiro; o Limiar de 6 dias é o próximo foco preventivo.'
        '</div>',
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Estoque atual", f"{stock}")
    k2.metric(
        "Prioridade de hoje",
        f"{priority_today}",
        help="Negócios com 1 ou 2 dias na fase.",
    )
    k3.metric(
        "Limiar · 6d",
        f"{threshold}",
        help="Estoque que entrará em Fora do SLA no dia seguinte se permanecer na fase.",
    )
    k4.metric(
        "Fora do SLA",
        f"{outside_sla}",
        help="7 dias ou mais, incluindo críticos.",
    )
    k5.metric("Críticos", f"{critical}", help="8 dias ou mais.")
    k6.metric(
        "Aging mediano",
        f"{median_age:.0f}d",
        help=f"Maior aging atual: {max_age} dias.",
    )

    i1, i2 = st.columns([1.15, 2], gap="large")

    with i1:
        st.markdown(
            f"""
<div class="aa-action">
    <div class="aa-action-kicker">PRÓXIMA MELHOR AÇÃO</div>
    <div class="aa-action-number">{priority_today}</div>
    <div class="aa-action-copy">
        negócios estão na janela prioritária de 1–2 dias.
        Comece pelos de 2 dias e depois pelos de 1 dia.
        O próximo foco é o Limiar de 6 dias.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with i2:
        lead_story = (
            f"<strong>{priority_today} negócios</strong> estão na janela que deve ser protegida primeiro. "
            if priority_today
            else "<strong>Não há negócios na janela prioritária de 1–2 dias neste momento.</strong> "
        )

        threshold_story = (
            f"Há <strong>{threshold} negócios no Limiar de 6 dias</strong>; "
            "se permanecerem na fase até amanhã, entrarão em Fora do SLA. "
            if threshold
            else "Não há negócios no Limiar de 6 dias neste momento. "
        )

        backlog_story = (
            f"O backlog total é de <strong>{backlog}</strong>, "
            f"com <strong>{critical}</strong> críticos."
            if backlog
            else "Não existe backlog atual na fase."
        )

        st.markdown(
            f"""
<div class="aa-insight">
    <strong>Leitura executiva</strong><br><br>
    {lead_story}{threshold_story}{backlog_story}<br><br>
    <span class="small-muted">
        Aging máximo: {max_age} dias · Fora do SLA: {outside_sla} negócios.
    </span>
</div>
""",
            unsafe_allow_html=True,
        )

    tab_health, tab_queue, tab_history = st.tabs(
        ["Saúde da fase", "Fila de Auditoria", "Histórico"]
    )

    with tab_health:
        st.markdown(
            '<div class="aa-section-kicker">SAÚDE DO FUNIL</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="aa-section-title">Como o estoque está envelhecendo?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="aa-section-copy">'
            'A saúde mede permanência na fase; a prioridade operacional é tratada separadamente.'
            '</div>',
            unsafe_allow_html=True,
        )

        health_counts = (
            current["status_saude"]
            .value_counts()
            .reindex(HEALTH_ORDER, fill_value=0)
            .reset_index()
        )
        health_counts.columns = ["Status", "Negócios"]

        fig = go.Figure(
            go.Bar(
                x=health_counts["Status"],
                y=health_counts["Negócios"],
                text=health_counts["Negócios"],
                textposition="outside",
                marker_color=[
                    HEALTH_COLORS[s] for s in health_counts["Status"]
                ],
                hovertemplate="<b>%{x}</b><br>%{y} negócios<extra></extra>",
            )
        )
        fig.update_layout(
            template="plotly_white",
            height=390,
            showlegend=False,
            margin=dict(l=10, r=10, t=25, b=15),
            xaxis_title="",
            yaxis_title="Negócios",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_yaxes(gridcolor="#ECEFF2")
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Dentro do SLA = 0–2 dias · Atenção = 3–5 · Limiar = 6 · "
            "Fora do SLA = 7 · Crítico = 8+."
        )

    with tab_queue:
        st.markdown(
            '<div class="aa-section-kicker">EXECUÇÃO</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="aa-section-title">Fila de Auditoria · Saúde dos negócios</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div class="aa-section-copy">
    Navegue pelos IDs conforme o estado de saúde da fase.
    Preserve primeiro a janela de 1–2 dias; em seguida, trate o Limiar de 6 dias
    antes que ele ultrapasse o SLA. Depois, avance sobre o backlog.
</div>
""",
            unsafe_allow_html=True,
        )

        filter_choice = st.radio(
            "Status da saúde",
            ["Críticos", "Elevados", "Atenção", "Dentro do SLA", "Todos"],
            horizontal=True,
            key=f"health_filter_{phase_key}",
        )

        filtered = current.copy()

        if filter_choice != "Todos":
            filtered = filtered.loc[
                filtered["grupo_fila"] == filter_choice
            ].copy()

        if filter_choice == "Todos":
            filtered = filtered.sort_values(
                ["ordem_prioridade", "aging_dias", "data_entrada_fase"],
                ascending=[True, False, True],
            )
        else:
            filtered = filtered.sort_values(
                ["aging_dias", "data_entrada_fase"],
                ascending=[False, True],
            )

        f1, f2, f3 = st.columns([1, 1, 2])
        f1.metric("IDs na seleção", len(filtered))
        f2.metric(
            "Maior aging",
            f"{int(filtered['aging_dias'].max())}d"
            if len(filtered)
            else "—",
        )
        f3.info(
            "Elevados reúne Limiar (6d) + Fora do SLA (7d). "
            "A tabela mantém o status exato."
        )

        left, right = st.columns([2.7, 1], gap="large")

        with left:
            display_df = filtered[
                [
                    "ID",
                    "aging_dias",
                    "status_saude",
                    "prioridade_operacional",
                    "data_entrada_fase",
                ]
            ].copy()

            display_df.columns = [
                "ID",
                "Aging (dias)",
                "Saúde",
                "Prioridade operacional",
                "Entrada na fase",
            ]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=560,
            )

        with right:
            st.markdown("#### IDs para atuação")
            ids_text = "\n".join(filtered["ID"].astype(str).tolist())
            st.code(
                ids_text or "Nenhum ID nesta seleção.",
                language=None,
            )

            st.download_button(
                "Baixar seleção",
                data=filtered.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"fila_{phase_key}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"download_queue_{phase_key}",
            )

    with tab_history:
        st.markdown(
            '<div class="aa-section-kicker">EVOLUÇÃO</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="aa-section-title">A operação está melhorando?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="aa-section-copy">'
            'Uma fotografia consolidada por dia; snapshots não são somados como novos negócios.'
            '</div>',
            unsafe_allow_html=True,
        )

        if history.empty or len(history) < 2:
            st.info(
                "O histórico ganha leitura comparativa após o segundo dia processado."
            )
        else:
            history = history.sort_values("data")

            h1, h2 = st.columns(2, gap="large")

            with h1:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=history["data"],
                        y=history["estoque"],
                        mode="lines+markers",
                        name="Estoque",
                        line=dict(color="#EBB346", width=3),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=history["data"],
                        y=history["backlog"],
                        mode="lines+markers",
                        name="Backlog",
                        line=dict(color="#D66B2C", width=2),
                    )
                )
                fig.update_layout(
                    template="plotly_white",
                    height=360,
                    title="Estoque x backlog",
                    margin=dict(l=10, r=10, t=55, b=15),
                    xaxis_title="",
                    yaxis_title="Negócios",
                    legend=dict(orientation="h", y=1.12),
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"history_stock_{phase_key}",
                )

            with h2:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=history["data"],
                        y=history["prioridade_hoje"],
                        mode="lines+markers",
                        name="Prioridade de hoje",
                        line=dict(color="#111318", width=3),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=history["data"],
                        y=history["fora_sla_total"],
                        mode="lines+markers",
                        name="Fora do SLA",
                        line=dict(color="#D64545", width=2),
                    )
                )
                fig.update_layout(
                    template="plotly_white",
                    height=360,
                    title="Prioridade x fora do SLA",
                    margin=dict(l=10, r=10, t=55, b=15),
                    xaxis_title="",
                    yaxis_title="Negócios",
                    legend=dict(orientation="h", y=1.12),
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"history_priority_{phase_key}",
                )

            latest_date = history["data"].max()

            last_7 = history.loc[
                history["data"] >= latest_date - pd.Timedelta(days=6)
            ].copy()

            month = history.loc[
                (history["data"].dt.year == latest_date.year)
                & (history["data"].dt.month == latest_date.month)
            ].copy()

            s1, s2, s3 = st.columns(3)
            s1.metric("Estoque atual", int(history.iloc[-1]["estoque"]))

            if len(last_7) >= 2:
                delta_7 = (
                    last_7.iloc[-1]["estoque"]
                    - last_7.iloc[0]["estoque"]
                )
                s2.metric(
                    "Variação · 7 dias",
                    f"{delta_7:+.0f}",
                    delta_color="inverse",
                )
            else:
                s2.metric("Variação · 7 dias", "—")

            if len(month) >= 2:
                delta_month = (
                    month.iloc[-1]["estoque"]
                    - month.iloc[0]["estoque"]
                )
                s3.metric(
                    "Variação · mês",
                    f"{delta_month:+.0f}",
                    delta_color="inverse",
                )
            else:
                s3.metric("Variação · mês", "—")

            history_show = history.sort_values(
                "data",
                ascending=False,
            ).copy()
            history_show["data"] = history_show["data"].dt.strftime(
                "%d/%m/%Y"
            )

            st.dataframe(
                history_show,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# CABEÇALHO + PAINÉIS SEPARADOS
# ============================================================

st.markdown(
    '<div class="aa-kicker">ANDRADE ALVES · INTELIGÊNCIA COMERCIAL</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="aa-title">Central · Funil de Marketing</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="aa-subtitle">'
    'Um único link, com bases independentes para Em Qualificação e Qualificado.'
    '</div>',
    unsafe_allow_html=True,
)

phase_tab_eq, phase_tab_qual = st.tabs(
    ["Em Qualificação", "Qualificado"]
)

with phase_tab_eq:
    render_phase_dashboard(
        "eq",
        PHASES["eq"],
        *phase_data["eq"],
    )

with phase_tab_qual:
    render_phase_dashboard(
        "qual",
        PHASES["qual"],
        *phase_data["qual"],
    )


st.divider()
st.caption(
    "Andrade Alves Advogados · Inteligência Comercial · "
    "Persistência: Google Sheets via Apps Script · "
    "Importação manual por fase"
)
