"""Correção de erros de digitação no número de unidades do Sivep-DDA."""

import pandas as pd

from src import config

COLUNAS_UNIDADES = ["nu_unidades_inf", "nu_usaude_sem"]


def corrigir_unidades(
    df: pd.DataFrame, limite: float = config.DDA_LIMITE_MEDIANA_UNIDADES, mostrar: bool = True
) -> pd.DataFrame:
    """
    Troca pela mediana do município o número de unidades acima de limite × a mediana.

    Critério do projeto, sem fonte oficial (decisão 0021).
    """
    df = df.copy()
    for coluna in COLUNAS_UNIDADES:
        mediana = df.groupby("municipio_ibge")[coluna].transform("median")
        erro = (mediana > 0) & (df[coluna] > limite * mediana)
        if mostrar and erro.any():
            print(f"\nCorreções em {coluna} (limite = {limite}× a mediana):")
            print(
                df.loc[erro, ["uf_sigla", "municipio_nome", "sem_epid_week", coluna]]
                .assign(corrigido_para=mediana[erro])
                .to_string(index=False)
            )
        df.loc[erro, coluna] = mediana[erro]
    return df
