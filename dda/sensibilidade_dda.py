"""
Sensibilidade da comparação de DDA entre o primeiro e o último ano à última
semana epidemiológica incluída (SE 22, 21 e 20), por causa do atraso de
digitação nas semanas finais.
"""

import pandas as pd

from dda import comum
from src import config


def main() -> None:
    primeiro, ultimo = min(config.DDA_ANOS), max(config.DDA_ANOS)
    for se_max in (22, 21, 20):
        totais = {}
        for ano in config.DDA_ANOS:
            semanal = pd.read_csv(comum.PROCESSADOS / f"dda_parauapebas_{ano}_semanal.csv")
            semanal = semanal[semanal["sem_epid_week"] <= se_max]
            casos = semanal["casos"].sum()
            totais[ano] = (casos, casos / semanal["nu_unidades_inf"].sum())
        variacao = 100 * (totais[ultimo][0] / totais[primeiro][0] - 1)
        print(
            f"SE 1 a {se_max}: {primeiro} = {totais[primeiro][0]} | "
            f"{ultimo} = {totais[ultimo][0]} | variação = {variacao:.1f}% | "
            f"por unidade: {totais[primeiro][1]:.2f} → {totais[ultimo][1]:.2f}"
        )


if __name__ == "__main__":
    main()
