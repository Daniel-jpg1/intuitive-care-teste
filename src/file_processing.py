from __future__ import annotations

import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Iterable, List

import pandas as pd


def extrair_arquivos_zip(arquivos_zip: Iterable[Path], destino_processed: Path) -> List[Path]:
    # Recebe uma lista de arquivos .zip e extrai o conteúdo para a pasta destino_processed. Retorna a lista de arquivos extraídos (CSV/TXT/XLS/XLSX).
    destino_processed.mkdir(parents=True, exist_ok=True)

    for zip_path in arquivos_zip:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(destino_processed)

    # Depois de extrair, varre a pasta e pega só arquivos de dados
    extraidos: List[Path] = []
    for ext in ("*.csv", "*.txt", "*.xls", "*.xlsx"):
        extraidos.extend(destino_processed.glob(ext))

    return extraidos


def identificar_arquivos_despesas(destino_processed: Path) -> List[Path]:
    # Identifica arquivos que potencialmente contêm dados de despesas/sinistros. Por enquanto, simplificamos: consideramos todos os arquivos CSV/TXT/XLS/XLSX extraídos dos zips como candidatos a terem informações relevantes.
    arquivos: List[Path] = []
    for ext in ("*.csv", "*.txt", "*.xls", "*.xlsx"):
        arquivos.extend(destino_processed.glob(ext))
    return arquivos


def _ler_arquivo_generico(caminho: Path) -> pd.DataFrame:
    # Lê um arquivo em formato CSV, TXT ou XLS/XLSX e devolve um DataFrame pandas. Tenta automaticamente: - encoding UTF-8 e, se falhar, Latin-1 - separadores ; e ,
    sufixo = caminho.suffix.lower()

    if sufixo in [".csv", ".txt"]:
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

    elif sufixo in [".xls", ".xlsx"]:
        try:
            return pd.read_excel(caminho)
        except Exception:
            # fallback genérico
            return pd.read_excel(caminho, engine="openpyxl")

    else:
        raise ValueError(f"Formato de arquivo não suportado: {caminho}")


def _normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    # Normaliza os nomes das colunas: - remove aspas e espaços extras - deixa tudo minúsculo - remove acentos - substitui caracteres não alfanuméricos por '_'
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


def _extrair_ano_trimestre_do_nome(caminho: Path) -> tuple[int | None, int | None]:
    # Tenta extrair ano e trimestre do nome do arquivo usando regex. Suporta formatos: - '2009_1_trimestre' - '2009-2-tri' - '1T2011', '2t2025', etc.
    nome = caminho.stem.lower()  # sem extensão

    # Formatos antigos: "2009_1_trimestre", "2011-2-tri"
    m_antigo = re.search(r"(?P<ano>\d{4}).*?(?P<tri>[1-4])\s*[_-]?\s*tri", nome)
    if m_antigo:
        ano = int(m_antigo.group("ano"))
        tri = int(m_antigo.group("tri"))
        return ano, tri

    # Formato novo: "1T2011", "2T2025"
    m_novo = re.search(r"(?P<tri>[1-4])\s*t\s*(?P<ano>\d{4})", nome)
    if m_novo:
        ano = int(m_novo.group("ano"))
        tri = int(m_novo.group("tri"))
        return ano, tri

    return None, None


def ler_e_normalizar_arquivos(arquivos_despesas: Iterable[Path]) -> pd.DataFrame:
    # Lê todos os arquivos de demonstrações contábeis dos trimestres selecionados e produz um DataFrame consolidado com: - RegistroANS   (REG_ANS) - Ano - Trimestre - ValorDespesas (VL_SALDO_FINAL, por enquanto sem filtro por tipo de conta) Posteriormente, vamos enriquecer esses dados com CNPJ, Razão Social, UF etc. usando o cadastro de operadoras.
    linhas: list[pd.DataFrame] = []

    for caminho in arquivos_despesas:
        try:
            df = _ler_arquivo_generico(caminho)
        except Exception:
            # Não conseguiu ler esse arquivo, segue pro próximo
            continue

        df = _normalizar_colunas(df)
        colunas = df.columns

        # Precisamos de pelo menos REG_ANS e VL_SALDO_FINAL
        if "reg_ans" not in colunas or "vl_saldo_final" not in colunas:
            # Este arquivo provavelmente não é o layout que esperamos
            continue

        ano, tri = _extrair_ano_trimestre_do_nome(caminho)

        temp = pd.DataFrame()
        temp["RegistroANS"] = df["reg_ans"].astype(str).str.strip()
        temp["ValorDespesas"] = pd.to_numeric(df["vl_saldo_final"], errors="coerce")
        temp["Ano"] = ano
        temp["Trimestre"] = tri

        linhas.append(temp)

    if not linhas:
        return pd.DataFrame(columns=["RegistroANS", "Ano", "Trimestre", "ValorDespesas"])

    resultado = pd.concat(linhas, ignore_index=True)
    return resultado


def gerar_consolidado_despesas(df: pd.DataFrame, caminho_csv: Path, caminho_zip: Path) -> None:
    # Salva o DataFrame consolidado em um CSV e também em um ZIP. O CSV conterá as colunas: - RegistroANS - Ano - Trimestre - ValorDespesas
    caminho_csv.parent.mkdir(parents=True, exist_ok=True)
    caminho_zip.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(caminho_csv, index=False, encoding="utf-8")

    with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(caminho_csv, arcname=caminho_csv.name)
