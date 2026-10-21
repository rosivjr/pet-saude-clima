"""Cloro e Escherichia coli por área de abrangência, ponto de coleta e mês."""

import logging

import pandas as pd

from src import config

from ._comum import _adicionar_wilson

logger = logging.getLogger(__name__)


def conformidade_por_area(df: pd.DataFrame) -> pd.DataFrame:
    """
    Não conformidade do cloro residual por área de abrangência, com IC.

    Áreas com menos de config.LIMIAR_AMOSTRAS_PROPORCAO amostras ficam na
    tabela, sinalizadas.
    """
    cloro = df[
        (df["PARAMETRO"] == config.PARAMETRO_CLORO)
        & df["resultado_numerico"].notna()
        & df["NO_AREA"].notna()
    ]

    if cloro.empty:
        logger.warning("Sem amostras de cloro com área identificada")
        return pd.DataFrame(
            columns=[
                "area",
                "amostras",
                "fora_do_padrao",
                "percentual_fora",
                "amostra_suficiente",
                "ic_inferior",
                "ic_superior",
            ]
        )

    resumo = (
        cloro.groupby("NO_AREA")["resultado_numerico"]
        .agg(
            amostras="size",
            fora_do_padrao=lambda s: int((s < config.CLORO_RESIDUAL_MINIMO).sum()),
        )
        .reset_index()
        .rename(columns={"NO_AREA": "area"})
    )

    resumo["percentual_fora"] = (resumo["fora_do_padrao"] / resumo["amostras"] * 100).round(1)
    resumo["amostra_suficiente"] = resumo["amostras"] >= config.LIMIAR_AMOSTRAS_PROPORCAO
    resumo = _adicionar_wilson(resumo, "fora_do_padrao", "amostras")

    return resumo.sort_values(
        ["percentual_fora", "amostras"], ascending=[False, False]
    ).reset_index(drop=True)


def _positividade(df: pd.DataFrame, coluna_grupo: str, rotulo: str) -> pd.DataFrame:
    """Positividade de E. coli agrupada por uma coluna, com IC de Wilson."""
    colunas = [rotulo, "amostras", "positivos", "percentual_positivo", "ic_inferior", "ic_superior"]
    micro = df[(df["PARAMETRO"] == config.PARAMETRO_E_COLI) & df[coluna_grupo].notna()]

    if micro.empty:
        return pd.DataFrame(columns=colunas)

    resumo = (
        micro.groupby(coluna_grupo)["resultado_texto"]
        .agg(amostras="size", positivos=lambda s: int((s == config.RESULTADO_PRESENTE).sum()))
        .reset_index()
        .rename(columns={coluna_grupo: rotulo})
    )
    resumo["percentual_positivo"] = (resumo["positivos"] / resumo["amostras"] * 100).round(1)
    return _adicionar_wilson(resumo, "positivos", "amostras")[colunas]


def ecoli_por_area(df: pd.DataFrame) -> pd.DataFrame:
    """Presença de Escherichia coli por área de abrangência (coluna NO_AREA), com IC."""
    resumo = _positividade(df, "NO_AREA", "area")
    if resumo.empty:
        logger.warning("Sem amostras de E. coli com área identificada")
        return resumo

    return resumo.sort_values(
        ["percentual_positivo", "amostras"], ascending=[False, False]
    ).reset_index(drop=True)


def ecoli_por_ponto(qualidade: pd.DataFrame) -> pd.DataFrame:
    """Presença de Escherichia coli por tipo de ponto de coleta, com IC."""
    resumo = _positividade(qualidade, "TP_PONTO_COLETA", "ponto")
    return resumo.sort_values("percentual_positivo", ascending=False).reset_index(drop=True)


def sazonalidade_ecoli(qualidade: pd.DataFrame) -> pd.DataFrame:
    """Positividade mensal para Escherichia coli, com IC."""
    colunas = [
        "ano",
        "mes",
        "amostras",
        "positivos",
        "percentual_positivo",
        "ic_inferior",
        "ic_superior",
    ]
    micro = qualidade[qualidade["PARAMETRO"] == config.PARAMETRO_E_COLI]

    if micro.empty:
        logger.warning("Sem amostras de E. coli para a série mensal")
        return pd.DataFrame(columns=colunas)

    resumo = (
        micro.groupby(["ano", "mes"])["resultado_texto"]
        .agg(amostras="size", positivos=lambda s: int((s == config.RESULTADO_PRESENTE).sum()))
        .reset_index()
    )
    resumo["percentual_positivo"] = (resumo["positivos"] / resumo["amostras"] * 100).round(1)
    return _adicionar_wilson(resumo, "positivos", "amostras")[colunas]
