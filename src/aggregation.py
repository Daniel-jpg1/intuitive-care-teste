from __future__ import annotations

from pathlib import Path
import zipfile

import pandas as pd


def agregar_despesas(caminho_enriquecido: Path, caminho_saida: Path) -> None:
    # Lê o CSV enriquecido (já com CNPJ, RazaoSocial, UF, Ano, Trimestre, ValorDespesas) e gera um CSV agregado por RazaoSocial e UF, contendo: - RazaoSocial - UF - TotalDespesas - MediaDespesas - DesvioPadraoDespesas
    df = pd.read_csv(caminho_enriquecido, encoding="utf-8")

    # Verificações básicas
    for col in ["RazaoSocial", "UF", "ValorDespesas"]:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no enriquecido: {col}")

    # Garante que o valor é numérico
    df["ValorDespesas"] = pd.to_numeric(df["ValorDespesas"], errors="coerce")
    df = df[df["ValorDespesas"].notna()]

    # Agrupamento por RazaoSocial + UF
    grupo = df.groupby(["RazaoSocial", "UF"])["ValorDespesas"]

    agregados = grupo.agg(["sum", "mean", "std"]).reset_index()
    agregados.rename(
        columns={
            "sum": "TotalDespesas",
            "mean": "MediaDespesas",
            "std": "DesvioPadraoDespesas",
        },
        inplace=True,
    )

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    agregados.to_csv(caminho_saida, index=False, encoding="utf-8")


def gerar_zip_final(final_dir: Path, zip_path: Path) -> None:
    # Gera o ZIP final do teste, contendo pelo menos: - consolidado_despesas.zip - despesas_agregadas.csv
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    arquivos_para_incluir: list[Path] = []

    consolidado_zip = final_dir / "consolidado_despesas.zip"
    if consolidado_zip.exists():
        arquivos_para_incluir.append(consolidado_zip)

    despesas_agregadas = final_dir / "despesas_agregadas.csv"
    if despesas_agregadas.exists():
        arquivos_para_incluir.append(despesas_agregadas)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho in arquivos_para_incluir:
            zf.write(caminho, arcname=caminho.name)
