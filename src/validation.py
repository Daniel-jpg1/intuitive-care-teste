from pathlib import Path
import pandas as pd


def _somente_digitos(cnpj: str) -> str:
    return "".join(ch for ch in cnpj if ch.isdigit())


def validar_cnpj(cnpj: str) -> bool:
    cnpj_limpo = _somente_digitos(cnpj)

    if len(cnpj_limpo) != 14:
        return False

    if cnpj_limpo == cnpj_limpo[0] * 14:
        return False

    def calc_dv(cnpj_base: str, pesos: list[int]) -> int:
        soma = sum(int(d) * p for d, p in zip(cnpj_base, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    base = cnpj_limpo[:12]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = calc_dv(base, pesos1)

    base2 = base + str(dv1)
    pesos2 = [6] + pesos1
    dv2 = calc_dv(base2, pesos2)

    return cnpj_limpo == base + str(dv1) + str(dv2)


def validar_dados_consolidados(caminho_csv_entrada: Path, caminho_csv_saida: Path) -> None:
    # Lê o CSV consolidado, aplica validações e salva um novo CSV 'limpo'. Se o CSV estiver vazio, apenas copia a estrutura.
    df = pd.read_csv(caminho_csv_entrada)

    # Se não houver linhas, só salva e sai
    if df.empty:
        caminho_csv_saida.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(caminho_csv_saida, index=False, encoding="utf-8")
        return

    for col in ["CNPJ", "RazaoSocial", "ValorDespesas"]:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente: {col}")

    df["CNPJ"] = df["CNPJ"].astype(str).str.strip()
    df["RazaoSocial"] = df["RazaoSocial"].astype(str).str.strip()

    df["CNPJValido"] = df["CNPJ"].apply(validar_cnpj)
    df["ValorDespesas"] = pd.to_numeric(df["ValorDespesas"], errors="coerce")

    df_filtrado = df[
        (df["CNPJValido"])
        & (df["RazaoSocial"] != "")
        & (df["ValorDespesas"].notna())
        & (df["ValorDespesas"] > 0)
    ].copy()

    if "CNPJValido" in df_filtrado.columns:
        df_filtrado.drop(columns=["CNPJValido"], inplace=True)

    caminho_csv_saida.parent.mkdir(parents=True, exist_ok=True)
    df_filtrado.to_csv(caminho_csv_saida, index=False, encoding="utf-8")