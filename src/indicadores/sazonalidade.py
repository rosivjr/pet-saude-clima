"""Chuva mensal e o padrão de cada mês do calendário: chuva, E. coli e internações."""

import pandas as pd

from src import config

from ._comum import _wilson_percentual


def precipitacao_mensal(precipitacao: pd.DataFrame) -> pd.DataFrame:
    """Chuva acumulada (mm) e dias com dado em cada mês do período."""
    if precipitacao.empty:
        return pd.DataFrame(columns=["ano", "mes", "precipitacao_mm", "dias_com_dado"])

    df = precipitacao.assign(ano=precipitacao["data"].dt.year, mes=precipitacao["data"].dt.month)
    # min_count=1: mês sem nenhum valor fica NaN, e não 0 mm.
    resumo = (
        df.groupby(["ano", "mes"])["precipitacao_mm"]
        .agg(precipitacao_mm=lambda s: s.sum(min_count=1), dias_com_dado="count")
        .reset_index()
    )
    resumo["precipitacao_mm"] = resumo["precipitacao_mm"].round(1)
    return resumo


def sazonalidade_comparada(
    chuva_mensal: pd.DataFrame,
    sazonal_ecoli: pd.DataFrame,
    serie_internacoes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Por mês do calendário: chuva média, positividade de E. coli e internações.

    Junta os anos do período para descrever o padrão de cada mês. É uma
    descrição lado a lado; não estima associação entre as colunas. Recebe
    os resultados de precipitacao_mensal, sazonalidade_ecoli e
    serie_mensal_internacoes (DRSAI).
    """
    # Meses do período sem internação não aparecem na série mensal; entram
    # aqui com zero para não inflar a média.
    periodo = pd.period_range(config.PERIODO_INICIO, config.PERIODO_FIM, freq="M")
    completa = pd.DataFrame({"ano": periodo.year, "mes": periodo.month})
    completa = completa.merge(
        serie_internacoes[["ano", "mes", "internacoes"]], on=["ano", "mes"], how="left"
    ).fillna({"internacoes": 0})

    linhas = []
    for mes in range(1, 13):
        chuva = chuva_mensal[chuva_mensal["mes"] == mes]
        ecoli = sazonal_ecoli[sazonal_ecoli["mes"] == mes]
        internacoes = completa[completa["mes"] == mes]

        amostras = int(ecoli["amostras"].sum()) if not ecoli.empty else 0
        positivos = int(ecoli["positivos"].sum()) if not ecoli.empty else 0
        ic_inf, ic_sup = _wilson_percentual(positivos, amostras)

        linhas.append(
            {
                "mes": mes,
                "chuva_media_mm": round(float(chuva["precipitacao_mm"].mean()), 1)
                if not chuva.empty
                else None,
                "anos_chuva": len(chuva),
                "ecoli_amostras": amostras,
                "ecoli_positivos": positivos,
                "ecoli_percentual": round(positivos / amostras * 100, 1) if amostras else None,
                "ecoli_ic_inferior": ic_inf,
                "ecoli_ic_superior": ic_sup,
                "meses_com_coleta": len(ecoli),
                "internacoes_media": round(float(internacoes["internacoes"].mean()), 1)
                if not internacoes.empty
                else None,
                "anos_internacao": len(internacoes),
            }
        )
    return pd.DataFrame(linhas)
