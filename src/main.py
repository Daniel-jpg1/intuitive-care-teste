from __future__ import annotations

from pathlib import Path

from api_ans import baixar_arquivos_dos_ultimos_tres_trimestres
from file_processing import (
    extrair_arquivos_zip,
    identificar_arquivos_despesas,
    ler_e_normalizar_arquivos,
    gerar_consolidado_despesas,
)
from enrichment import baixar_cadastro_operadoras, enriquecer_consolidado_com_cadastro
from aggregation import agregar_despesas, gerar_zip_final
from validation import validar_dados_consolidados


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    final_dir = data_dir / "final"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    # 1. Baixar zips dos 3 últimos trimestres
    print("Baixando arquivos dos últimos 3 trimestres...")
    zip_paths = baixar_arquivos_dos_ultimos_tres_trimestres(raw_dir)
    print(f"{len(zip_paths)} arquivos .zip baixados.")

    # 2. Extrair zips
    print("Extraindo arquivos .zip...")
    arquivos_extraidos = extrair_arquivos_zip(zip_paths, processed_dir)
    print(f"{len(arquivos_extraidos)} arquivos extraídos.")

    # 3. Identificar arquivos de despesas/sinistros
    print("Identificando arquivos de despesas/sinistros...")
    arquivos_despesas = identificar_arquivos_despesas(processed_dir)
    print(f"{len(arquivos_despesas)} arquivos de despesas identificados.")

    # 4. Ler e normalizar
    print("Lendo e normalizando arquivos de despesas...")
    df_normalizado = ler_e_normalizar_arquivos(arquivos_despesas)
    print(f"{len(df_normalizado)} linhas normalizadas.")

    if df_normalizado.empty:
        print("Nenhuma linha normalizada. Verifique os arquivos baixados e a lógica de mapeamento de colunas.")
        return

    # 5. Gerar consolidado_despesas.csv + zip
    consolidado_csv = processed_dir / "consolidado_despesas.csv"
    consolidado_zip = final_dir / "consolidado_despesas.zip"
    print("Gerando consolidado_despesas.csv e zip...")
    gerar_consolidado_despesas(df_normalizado, consolidado_csv, consolidado_zip)

    # 6. Baixar cadastro de operadoras
    cadastro_csv = processed_dir / "cadastro_operadoras.csv"
    print("Baixando cadastro de operadoras ativas...")
    baixar_cadastro_operadoras(cadastro_csv)

    # 7. Enriquecer consolidado com cadastro (trazendo CNPJ, RazaoSocial, UF etc.)
    enriquecido_csv = processed_dir / "consolidado_enriquecido.csv"
    print("Enriquecendo consolidado com cadastro de operadoras...")
    enriquecer_consolidado_com_cadastro(
        consolidado_csv,
        cadastro_csv,
        enriquecido_csv,
    )

    # 7.5. Validar dados enriquecidos (CNPJ, RazaoSocial, ValorDespesas)
    enriquecido_validado_csv = processed_dir / "consolidado_enriquecido_validado.csv"
    print("Validando dados consolidados (CNPJ, RazaoSocial, ValorDespesas)...")
    validar_dados_consolidados(enriquecido_csv, enriquecido_validado_csv)

    # 8. Agregar despesas por RazaoSocial/UF usando o arquivo validado
    despesas_agregadas_csv = final_dir / "despesas_agregadas.csv"
    print("Gerando despesas agregadas...")
    agregar_despesas(enriquecido_validado_csv, despesas_agregadas_csv)

    # 9. Gerar ZIP final
    zip_final = final_dir / "Teste_seu_nome.zip"
    print("Gerando ZIP final do teste...")
    gerar_zip_final(final_dir, zip_final)

    print("Pipeline concluído com sucesso.")


if __name__ == "__main__":
    main()
