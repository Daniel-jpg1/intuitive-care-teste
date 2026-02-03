from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


CADASTRO_BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"


def _get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def baixar_cadastro_operadoras(destino_csv: Path) -> None:
    # Acessa a pasta de operadoras ativas da ANS e baixa o CSV mais recente. O arquivo baixado é salvo em destino_csv com o nome 'cadastro_operadoras.csv'.
    destino_csv.parent.mkdir(parents=True, exist_ok=True)

    soup = _get_soup(CADASTRO_BASE_URL)
    links = soup.find_all("a")

    csv_links: list[str] = []
    for link in links:
        href = link.get("href")
        if href and href.lower().endswith(".csv"):
            csv_links.append(href)

    if not csv_links:
        raise RuntimeError("Nenhum arquivo CSV encontrado em operadoras_de_plano_de_saude_ativas/")

    # Por simplicidade, pega o último da lista (tende a ser o mais recente)
    csv_nome = csv_links[-1]
    url_csv = CADASTRO_BASE_URL + csv_nome

    resp = requests.get(url_csv, stream=True)
    resp.raise_for_status()

    with open(destino_csv, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def _normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    # Normaliza nomes de colunas: - tira aspas - deixa minúsculo - remove acentos - troca qualquer coisa não [a-z0-9] por "_"
    colunas_novas: list[str] = []

    for col in df.columns:
        nome = str(col).strip().strip('"').lower()
        nome = unicodedata.normalize("NFKD", nome)
        nome = "".join(ch for ch in nome if not unicodedata.combining(ch))
        nome = re.sub(r"[^a-z0-9]+", "_", nome)
        nome = nome.strip("_")
        colunas_novas.append(nome)

    df.columns = colunas_novas
    return df


def _ler_csv_generico(caminho: Path) -> pd.DataFrame:
    # Tenta ler o CSV de cadastro tentando combinações de encoding e separador.
    erros: list[Exception] = []
    for encoding in ("utf-8", "latin1"):
        for sep in (";", ","):
            try:
                return pd.read_csv(
                    caminho,
                    sep=sep,
                    engine="python",
                    encoding=encoding,
                )
            except Exception as e:
                erros.append(e)
    raise erros[-1] if erros else ValueError(f"Não foi possível ler o arquivo: {caminho}")


def enriquecer_consolidado_com_cadastro(
    caminho_consolidado: Path,
    caminho_cadastro: Path,
    caminho_saida: Path,
) -> None:
    # Faz o join entre: - consolidado_despesas.csv  (RegistroANS, Ano, Trimestre, ValorDespesas) - cadastro_operadoras.csv   (REGISTRO_OPERADORA, CNPJ, Razao_Social, Modalidade, UF, ...) usando: RegistroANS (consolidado)  <->  REGISTRO_OPERADORA (cadastro) Saída: CSV com colunas: - RegistroANS - CNPJ - RazaoSocial - Modalidade - UF - Ano - Trimestre - ValorDespesas
    
    # Lê consolidado
    df_cons = pd.read_csv(caminho_consolidado, encoding="utf-8")
    df_cons = _normalizar_colunas(df_cons)
    # Esperamos: registroans, valordespesas, ano, trimestre

    # Lê cadastro
    df_cad = _ler_csv_generico(caminho_cadastro)
    df_cad = _normalizar_colunas(df_cad)
    # Pelo seu head, as colunas ficam:
    # registro_operadora, cnpj, razao_social, nome_fantasia, modalidade, ..., uf, ...

    cols_cons = list(df_cons.columns)
    cols_cad = list(df_cad.columns)

    # Garante que as colunas que precisamos existem
    if "registroans" not in cols_cons:
        raise ValueError("Consolidado não possui coluna 'RegistroANS' normalizada ('registroans').")

    if "registro_operadora" not in cols_cad:
        raise ValueError("Cadastro não possui coluna 'REGISTRO_OPERADORA' normalizada ('registro_operadora').")

    # Converte chaves de join para string, garantindo mesma base de comparação
    df_cons["registroans"] = df_cons["registroans"].astype(str).str.strip()
    df_cad["registro_operadora"] = df_cad["registro_operadora"].astype(str).str.strip()

    # Faz join LEFT: mantemos todas as linhas do consolidado
    df_merged = df_cons.merge(
        df_cad,
        left_on="registroans",
        right_on="registro_operadora",
        how="left",
    )

    # Monta dataframe final com nomes bonitos
    df_final = pd.DataFrame()
    df_final["RegistroANS"] = df_merged["registroans"].astype(str)

    # CNPJ
    if "cnpj" in df_merged.columns:
        df_final["CNPJ"] = df_merged["cnpj"].astype(str)
    else:
        df_final["CNPJ"] = ""

    # Razão Social
    if "razao_social" in df_merged.columns:
        df_final["RazaoSocial"] = df_merged["razao_social"].astype(str)
    else:
        df_final["RazaoSocial"] = ""

    # Modalidade
    if "modalidade" in df_merged.columns:
        df_final["Modalidade"] = df_merged["modalidade"].astype(str)
    else:
        df_final["Modalidade"] = ""

    # UF
    if "uf" in df_merged.columns:
        df_final["UF"] = df_merged["uf"].astype(str)
    else:
        df_final["UF"] = ""

    # Ano, Trimestre, ValorDespesas
    df_final["Ano"] = df_merged["ano"] if "ano" in df_merged.columns else None
    df_final["Trimestre"] = df_merged["trimestre"] if "trimestre" in df_merged.columns else None
    df_final["ValorDespesas"] = df_merged["valordespesas"] if "valordespesas" in df_merged.columns else None

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(caminho_saida, index=False, encoding="utf-8")
