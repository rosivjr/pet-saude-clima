"""
Casos semanais de DDA (Sivep-DDA) de Parauapebas e do Brasil nos anos de
config.DDA_ANOS: confere o dicionário das colunas, mostra totais agregados e
grava as séries semanais em data/processed.
"""

import pandas as pd

from dda import comum
from src import config


def main() -> None:
    comum.PROCESSADOS.mkdir(parents=True, exist_ok=True)
    dicionario = pd.read_csv(comum.DICIONARIO / "sivep_dda_codebook.csv")
    print("Colunas do codebook:", dicionario.columns.tolist())
    alvo = (
        config.DDA_FAIXAS
        + config.DDA_PLANOS
        + ["nu_usaude_sem", "nu_unidades_inf", "lo_surto", "nu_surto"]
    )
    print(dicionario[dicionario.iloc[:, 0].isin(alvo)].to_string())

    for ano in config.DDA_ANOS:
        df = comum.ler_ano(ano)
        df["casos"] = df[config.DDA_FAIXAS].sum(axis=1)
        df["casos_planos"] = df[config.DDA_PLANOS].sum(axis=1)

        print(f"\n==================== {ano} ====================")
        print("Última semana epidemiológica na base:", df["sem_epid_week"].max())

        pbs = df[df["municipio_ibge"] == config.MUNICIPIO_IBGE_6].sort_values("sem_epid_week")

        duplicadas = pbs.duplicated(subset=["sem_epid_week"]).sum()
        print("Semanas duplicadas em Parauapebas:", duplicadas)

        colunas = (
            ["sem_epid_week", "casos"]
            + config.DDA_FAIXAS
            + config.DDA_PLANOS
            + ["nu_usaude_sem", "nu_unidades_inf", "lo_surto"]
        )
        semanal = pbs.groupby("sem_epid_week", as_index=False).agg(
            {c: "sum" for c in colunas[1:-1]} | {"lo_surto": "first"}
        )
        semanal.to_csv(comum.PROCESSADOS / f"dda_parauapebas_{ano}_semanal.csv", index=False)

        print("\nParauapebas – semanas com registro:", semanal["sem_epid_week"].nunique())
        print("Total de casos:", semanal["casos"].sum())
        print("Casos por faixa etária:\n", semanal[config.DDA_FAIXAS].sum().to_string())
        print("Casos por plano de tratamento:\n", semanal[config.DDA_PLANOS].sum().to_string())
        print(
            "Unidades implantadas (valores distintos):", sorted(semanal["nu_usaude_sem"].unique())
        )
        print(
            "Unidades informantes – mínimo e máximo:",
            semanal["nu_unidades_inf"].min(),
            semanal["nu_unidades_inf"].max(),
        )
        print("Semanas com surto registrado:", (semanal["lo_surto"] == "Sim").sum())
        print(
            "Diferença entre soma das faixas e soma dos planos:",
            int(semanal["casos"].sum() - pbs["casos_planos"].sum()),
        )

        brasil = df[config.DDA_FAIXAS + config.DDA_PLANOS + ["casos"]].sum()
        para = df[df["uf_ibge"] == config.UF_IBGE][["casos"]].sum()
        print("\nBrasil – total de casos:", int(brasil["casos"]))
        print(
            "Brasil – municípios que informaram ao menos uma semana:",
            df.loc[df["casos"] > 0, "municipio_ibge"].nunique(),
        )
        print("Pará – total de casos:", int(para["casos"]))

        brasil_semanal = df.groupby("sem_epid_week", as_index=False)["casos"].sum()
        brasil_semanal.to_csv(comum.PROCESSADOS / f"dda_brasil_{ano}_semanal.csv", index=False)

    print("\nArquivos salvos em data/processed/")


if __name__ == "__main__":
    main()
