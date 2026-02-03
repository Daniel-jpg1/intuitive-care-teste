from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"

CONSOLIDADO_ENRIQUECIDO_CSV = PROCESSED_DIR / "consolidado_enriquecido.csv"
DESPESAS_AGREGADAS_CSV = FINAL_DIR / "despesas_agregadas.csv"


# -------------------------------------------------
# Modelos de resposta (Pydantic)
# -------------------------------------------------

class OperadoraResumo(BaseModel):
    cnpj: str
    razao_social: str
    modalidade: Optional[str] = None
    uf: Optional[str] = None


class OperadoraDetalhe(BaseModel):
    cnpj: str
    razao_social: str
    modalidade: Optional[str] = None
    uf: Optional[str] = None
    total_despesas: float
    media_despesas: Optional[float] = None
    desvio_padrao_despesas: Optional[float] = None


class DespesaItem(BaseModel):
    ano: int
    trimestre: int
    valor_despesas: float


class EstatisticasResponse(BaseModel):
    total_despesas: float
    media_despesas: float
    top5_operadoras: List[OperadoraDetalhe]


class PaginatedResponse(BaseModel):
    data: List[OperadoraResumo]
    page: int
    limit: int
    total: int


# -------------------------------------------------
# Inicialização do app
# -------------------------------------------------

app = FastAPI(
    title="Intuitive Care - Teste Técnico",
    description="API de leitura dos dados consolidados de operadoras e despesas.",
    version="1.0.0",
)

# Habilita CORS para facilitar testes com frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # em produção deveria ser mais restrito
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Carregamento dos dados em memória
# -------------------------------------------------

df_enriquecido: Optional[pd.DataFrame] = None
df_agregado: Optional[pd.DataFrame] = None


def carregar_dados() -> None:
    global df_enriquecido, df_agregado

    if not CONSOLIDADO_ENRIQUECIDO_CSV.exists():
        raise RuntimeError(f"Arquivo não encontrado: {CONSOLIDADO_ENRIQUECIDO_CSV}")

    if not DESPESAS_AGREGADAS_CSV.exists():
        raise RuntimeError(f"Arquivo não encontrado: {DESPESAS_AGREGADAS_CSV}")

    df_enriquecido = pd.read_csv(CONSOLIDADO_ENRIQUECIDO_CSV, encoding="utf-8")
    df_agregado = pd.read_csv(DESPESAS_AGREGADAS_CSV, encoding="utf-8")

    # Normalizações básicas
    for col in ("CNPJ", "RazaoSocial", "Modalidade", "UF"):
        if col in df_enriquecido.columns:
            df_enriquecido[col] = df_enriquecido[col].astype(str).str.strip()

    for col in ("RazaoSocial", "UF"):
        if col in df_agregado.columns:
            df_agregado[col] = df_agregado[col].astype(str).str.strip()


@app.on_event("startup")
def on_startup() -> None:
    carregar_dados()


# -------------------------------------------------
# Rotas
# -------------------------------------------------

@app.get("/api/operadoras", response_model=PaginatedResponse)
def listar_operadoras(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    busca: Optional[str] = Query(None, description="Busca por CNPJ ou Razão Social"),
):
    """
    Lista operadoras com paginação (offset-based).
    Busca opcional por CNPJ ou Razão Social.
    """
    if df_enriquecido is None:
        raise HTTPException(status_code=500, detail="Dados não carregados")

    df = df_enriquecido.copy()

    # Agrupa por CNPJ + RazaoSocial + Modalidade + UF para ter uma linha por operadora
    df_grouped = (
        df.groupby(["CNPJ", "RazaoSocial", "Modalidade", "UF"], dropna=False)
        .size()
        .reset_index()
        .rename(columns={0: "qtd_registros"})
    )

    if busca:
        busca_lower = busca.lower()
        df_grouped = df_grouped[
            df_grouped["CNPJ"].str.lower().str.contains(busca_lower)
            | df_grouped["RazaoSocial"].str.lower().str.contains(busca_lower)
        ]

    total = len(df_grouped)

    offset = (page - 1) * limit
    df_page = df_grouped.iloc[offset : offset + limit]

    data = [
        OperadoraResumo(
            cnpj=row["CNPJ"],
            razao_social=row["RazaoSocial"],
            modalidade=row.get("Modalidade"),
            uf=row.get("UF"),
        )
        for _, row in df_page.iterrows()
    ]

    return PaginatedResponse(
        data=data,
        page=page,
        limit=limit,
        total=total,
    )


@app.get("/api/operadoras/{cnpj}", response_model=OperadoraDetalhe)
def detalhar_operadora(cnpj: str):
    """
    Retorna detalhes de uma operadora específica, incluindo dados agregados de despesas.
    """
    if df_enriquecido is None or df_agregado is None:
        raise HTTPException(status_code=500, detail="Dados não carregados")

    # Normaliza CNPJ
    cnpj_str = str(cnpj).strip()

    df_op = df_enriquecido[df_enriquecido["CNPJ"] == cnpj_str]
    if df_op.empty:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")

    # Usa primeira linha como base de dados cadastrais
    base = df_op.iloc[0]

    # Pega agregados pela RazaoSocial + UF
    razao = base["RazaoSocial"]
    uf = base["UF"]

    df_ag = df_agregado[
        (df_agregado["RazaoSocial"] == razao) & (df_agregado["UF"] == uf)
    ]

    if df_ag.empty:
        total = 0.0
        media = None
        desvio = None
    else:
        ag = df_ag.iloc[0]
        total = float(ag["TotalDespesas"])
        media = float(ag["MediaDespesas"]) if not pd.isna(ag["MediaDespesas"]) else None
        desvio = (
            float(ag["DesvioPadraoDespesas"])
            if not pd.isna(ag["DesvioPadraoDespesas"])
            else None
        )

    return OperadoraDetalhe(
        cnpj=cnpj_str,
        razao_social=str(base["RazaoSocial"]),
        modalidade=str(base.get("Modalidade")) if "Modalidade" in base else None,
        uf=str(base.get("UF")) if "UF" in base else None,
        total_despesas=total,
        media_despesas=media,
        desvio_padrao_despesas=desvio,
    )


@app.get("/api/operadoras/{cnpj}/despesas", response_model=List[DespesaItem])
def historico_despesas_operadora(cnpj: str):
    """
    Retorna histórico de despesas (Ano/Trimestre/Valor) de uma operadora.
    """
    if df_enriquecido is None:
        raise HTTPException(status_code=500, detail="Dados não carregados")

    cnpj_str = str(cnpj).strip()

    df_op = df_enriquecido[df_enriquecido["CNPJ"] == cnpj_str]
    if df_op.empty:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")

    # Faz um agrupamento por ano/trimestre somando ValorDespesas
    df_hist = (
        df_op.groupby(["Ano", "Trimestre"])["ValorDespesas"]
        .sum()
        .reset_index()
        .sort_values(["Ano", "Trimestre"])
    )

    itens = [
        DespesaItem(
            ano=int(row["Ano"]),
            trimestre=int(row["Trimestre"]),
            valor_despesas=float(row["ValorDespesas"]),
        )
        for _, row in df_hist.iterrows()
    ]

    return itens


@app.get("/api/estatisticas", response_model=EstatisticasResponse)
def estatisticas():
    """
    Retorna estatísticas agregadas:
    - total geral de despesas
    - média geral
    - top 5 operadoras (por TotalDespesas, via tabela agregada)
    """
    if df_enriquecido is None or df_agregado is None:
        raise HTTPException(status_code=500, detail="Dados não carregados")

    # Total e média global
    df_valid = df_enriquecido.copy()
    df_valid["ValorDespesas"] = pd.to_numeric(
        df_valid["ValorDespesas"], errors="coerce"
    )
    df_valid = df_valid[df_valid["ValorDespesas"].notna()]
    total = float(df_valid["ValorDespesas"].sum())
    media = float(df_valid["ValorDespesas"].mean()) if not df_valid.empty else 0.0

    # Top 5 operadoras (usando agregados)
    df_top5 = df_agregado.sort_values("TotalDespesas", ascending=False).head(5)

    top5: List[OperadoraDetalhe] = []
    for _, row in df_top5.iterrows():
        razao = str(row["RazaoSocial"])
        uf = str(row["UF"])

        # tenta achar um CNPJ representativo para essa Razao/UF
        df_match = df_enriquecido[
            (df_enriquecido["RazaoSocial"] == razao)
            & (df_enriquecido["UF"] == uf)
        ]
        if df_match.empty:
            cnpj = ""
            modalidade = None
        else:
            base = df_match.iloc[0]
            cnpj = str(base["CNPJ"])
            modalidade = str(base.get("Modalidade")) if "Modalidade" in base else None

        top5.append(
            OperadoraDetalhe(
                cnpj=cnpj,
                razao_social=razao,
                modalidade=modalidade,
                uf=uf,
                total_despesas=float(row["TotalDespesas"]),
                media_despesas=float(row["MediaDespesas"])
                if not pd.isna(row["MediaDespesas"])
                else None,
                desvio_padrao_despesas=float(row["DesvioPadraoDespesas"])
                if not pd.isna(row["DesvioPadraoDespesas"])
                else None,
            )
        )

    return EstatisticasResponse(
        total_despesas=total,
        media_despesas=media,
        top5_operadoras=top5,
    )
