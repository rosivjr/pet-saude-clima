"""
Internações por diarreia (A00–A09) e hepatite A (B15), SIH-RD, nos anos de
config.DDA_ANOS.
"""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from sih import comum
from src import config
from src.transformacoes import filtrar_aih_normal

COLUNAS = ["MUNIC_RES", "DIAG_PRINC", "DT_INTER", "IDENT"]


def main() -> None:
    config.DADOS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    # Só os arquivos do grupo RD (internações)
    arquivos = comum.arquivos_rdpa()
    print(f"Arquivos RD encontrados: {len(arquivos)}")
    print("Primeiro e último:", Path(arquivos[0]).name, "|", Path(arquivos[-1]).name)

    # Conferir colunas antes de calcular (só o esquema, sem ler os dados)
    colunas_arquivo = pq.read_schema(arquivos[0]).names
    faltando = [c for c in COLUNAS if c not in colunas_arquivo]
    if faltando:
        print("Colunas disponíveis:", colunas_arquivo)
        raise SystemExit(f"Colunas ausentes no SIH: {faltando}")

    df = pd.concat((comum.ler_rd(a, COLUNAS) for a in arquivos), ignore_index=True)

    print("\nTipos de AIH (IDENT):")
    print(df["IDENT"].value_counts().to_string())

    # Só AIH do tipo 1 (internação), para não contar continuações (decisão 0009)
    df = filtrar_aih_normal(df)
    print("Datas de internação inválidas:", df["data_internacao"].isna().sum())

    df["grupo"] = None
    df.loc[df["cid3"].isin(config.CID_RELATORIO_DDA["diarreia"]), "grupo"] = "Diarreia (A00–A09)"
    df.loc[df["cid3"].isin(config.CID_RELATORIO_DDA["hepatite_a"]), "grupo"] = "Hepatite A (B15)"
    df = comum.filtrar_anos_dda(df)
    df = df[df["grupo"].notna()]

    # Nome do recorte no texto e no arquivo (sem acento)
    recortes = [
        ("Parauapebas", "parauapebas", df[df["MUNIC_RES"] == config.MUNICIPIO_IBGE_6_STR]),
        ("Pará", "para", df),
    ]
    for nome, arquivo, recorte in recortes:
        tabela = recorte.groupby(["grupo", "ano", "mes"]).size().unstack("mes", fill_value=0)
        tabela["Total"] = tabela.sum(axis=1)
        print(f"\n===== {nome}: internações por mês da internação =====")
        print(tabela.to_string())
        tabela.to_csv(config.DADOS_PROCESSADOS / f"sih_{arquivo}_mensal.csv")

    print("\nTabelas salvas em data/processed/")


if __name__ == "__main__":
    main()
