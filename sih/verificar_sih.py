"""Checagem de codificação: internações por desidratação (E86) e por diarreia (A00–A09)."""

import pandas as pd

from sih import comum
from src import config
from src.transformacoes import filtrar_aih_normal

COLUNAS = ["MUNIC_RES", "DIAG_PRINC", "DT_INTER", "IDENT"]


def main() -> None:
    # Internações por desidratação (E86) e por diarreia (A00–A09), só AIH do
    # tipo 1 (decisão 0009)
    df = pd.concat((comum.ler_rd(a, COLUNAS) for a in comum.arquivos_rdpa()), ignore_index=True)
    df = comum.filtrar_anos_dda(filtrar_aih_normal(df))

    grupos = {
        "Diarreia (A00–A09)": df["cid3"].isin(config.CID_RELATORIO_DDA["diarreia"]),
        "Desidratação (E86)": df["cid3"].isin(config.CID_RELATORIO_DDA["desidratacao"]),
    }
    residentes = df["MUNIC_RES"] == config.MUNICIPIO_IBGE_6_STR
    for nome, recorte in [("Parauapebas", residentes), ("Pará", True)]:
        print(f"\n===== {nome} =====")
        for grupo, filtro in grupos.items():
            contagem = df[filtro & recorte].groupby("ano").size()
            print(f"{grupo}: {contagem.to_dict()}")

    # Total de internações de moradores de Parauapebas, para referência
    total = df[residentes].groupby("ano").size()
    print(f"\nParauapebas – todas as internações pelo SUS: {total.to_dict()}")


if __name__ == "__main__":
    main()
