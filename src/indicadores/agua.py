"""Conformidade e positividade das amostras de água do SISAGUA (Portaria GM/MS nº 888/2021)."""

import logging
from dataclasses import dataclass

import pandas as pd

from src import config

from ._comum import _adicionar_wilson, _wilson_percentual

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoConformidade:
    """Conformidade de um parâmetro; percentual e IC 95% de Wilson em escala 0 a 100."""

    parametro: str
    limite_minimo: float | None  # limites legais, na unidade do parâmetro
    limite_maximo: float | None
    unidade: str
    total_amostras: int  # só amostras com resultado válido
    fora_do_padrao: int
    percentual_fora: float
    ic_inferior: float = 0.0
    ic_superior: float = 0.0


def avaliar_conformidade_agua(df: pd.DataFrame) -> list[ResultadoConformidade]:
    """
    Conformidade de cloro residual, turbidez e pH, um resultado por parâmetro.

    Limites da Portaria GM/MS nº 888/2021, lidos do config. Amostras sem
    resultado numérico válido ficam fora do denominador.
    """
    avaliacoes = [
        (
            config.PARAMETRO_CLORO,
            (config.CLORO_RESIDUAL_MINIMO, None, "mg/L"),
            lambda s: s < config.CLORO_RESIDUAL_MINIMO,
        ),
        (
            config.PARAMETRO_TURBIDEZ,
            (None, config.TURBIDEZ_MAXIMA, "uT"),
            lambda s: s > config.TURBIDEZ_MAXIMA,
        ),
        (
            config.PARAMETRO_PH,
            (config.PH_MINIMO, config.PH_MAXIMO, ""),
            lambda s: (s < config.PH_MINIMO) | (s > config.PH_MAXIMO),
        ),
    ]

    resultados = []

    for parametro, (minimo, maximo, unidade), violou in avaliacoes:
        valores = df.loc[df["PARAMETRO"] == parametro, "resultado_numerico"].dropna()

        if valores.empty:
            logger.warning("Nenhuma amostra válida para %s", parametro)
            continue

        fora = int(violou(valores).sum())
        total = int(len(valores))
        inferior, superior = _wilson_percentual(fora, total)

        resultados.append(
            ResultadoConformidade(
                parametro=parametro,
                limite_minimo=minimo,
                limite_maximo=maximo,
                unidade=unidade,
                total_amostras=total,
                fora_do_padrao=fora,
                percentual_fora=round(fora / total * 100, 1),
                ic_inferior=inferior,
                ic_superior=superior,
            )
        )

    return resultados


def avaliar_microbiologico(df: pd.DataFrame) -> pd.DataFrame:
    """
    Percentual de amostras com presença em cada parâmetro microbiológico, com IC de Wilson.

    A Portaria 888/2021 avalia coliformes totais no conjunto mensal de amostras
    do responsável pelo sistema; as amostras do SISAGUA são da vigilância, e por
    isso o indicador é a presença, sem aplicar o critério mensal.
    """
    micro = df[df["PARAMETRO"].isin(config.PARAMETROS_MICROBIOLOGICOS)]

    resumo = (
        micro.groupby("PARAMETRO")["resultado_texto"]
        .agg(
            total="size",
            presentes=lambda s: (s == config.RESULTADO_PRESENTE).sum(),
        )
        .reset_index()
    )

    resumo["percentual_presenca"] = (resumo["presentes"] / resumo["total"] * 100).round(1)

    return _adicionar_wilson(resumo, "presentes", "total")


def serie_mensal(df: pd.DataFrame, parametro: str) -> pd.DataFrame:
    """Amostras, média e mediana por ano e mês de um parâmetro numérico (nome exato)."""
    recorte = df[(df["PARAMETRO"] == parametro) & df["resultado_numerico"].notna()]

    if recorte.empty:
        logger.warning("Sem dados para a série mensal de %s", parametro)
        return pd.DataFrame(columns=["ano", "mes", "amostras", "media", "mediana"])

    return (
        recorte.groupby(["ano", "mes"])["resultado_numerico"]
        .agg(amostras="size", media="mean", mediana="median")
        .round(3)
        .reset_index()
    )


def serie_anual_agua(df: pd.DataFrame) -> pd.DataFrame:
    """
    Proporção de amostras fora do padrão (cloro) ou com presença
    (coliformes totais e E. coli) por ano, com IC de Wilson.

    O número de amostras de cada ano vai junto, pois o volume de coleta
    varia muito entre anos (ex.: cloro residual em 2023).
    """
    definicoes = [
        (
            "Cloro abaixo do mínimo legal",
            config.PARAMETRO_CLORO,
            "resultado_numerico",
            lambda s: s < config.CLORO_RESIDUAL_MINIMO,
        ),
        (
            "Coliformes totais presentes",
            config.PARAMETRO_COLIFORMES,
            "resultado_texto",
            lambda s: s == config.RESULTADO_PRESENTE,
        ),
        (
            "Escherichia coli presente",
            config.PARAMETRO_E_COLI,
            "resultado_texto",
            lambda s: s == config.RESULTADO_PRESENTE,
        ),
    ]

    linhas = []
    for indicador, parametro, coluna, condicao in definicoes:
        recorte = df[(df["PARAMETRO"] == parametro) & df[coluna].notna()]
        for ano, bloco in recorte.groupby("ano"):
            total = len(bloco)
            fora = int(condicao(bloco[coluna]).sum())
            linhas.append(
                {
                    "indicador": indicador,
                    "ano": int(ano),
                    "amostras": total,
                    "fora": fora,
                    "percentual": round(fora / total * 100, 1),
                }
            )

    resultado = pd.DataFrame(
        linhas,
        columns=["indicador", "ano", "amostras", "fora", "percentual"],
    )
    return _adicionar_wilson(resultado, "fora", "amostras")
