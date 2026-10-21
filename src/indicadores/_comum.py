"""Pessoa-tempo, meses comuns, anos parciais e intervalos de Wilson usados por vários assuntos."""

import calendar
from datetime import date

import pandas as pd

from src import config
from src.estatistica import ic_wilson, pessoa_tempo


def pessoa_ano_periodo(fim: date | None = None) -> float:
    """Pessoas-ano de config.PERIODO_INICIO até fim (padrão: config.PERIODO_FIM)."""
    return pessoa_tempo(config.POPULACAO_ANUAL, config.PERIODO_INICIO, fim or config.PERIODO_FIM)


def _ultimo_dia(ano: int, mes: int) -> date:
    return date(ano, mes, calendar.monthrange(ano, mes)[1])


def meses_comuns(inicio: date | None = None, fim: date | None = None) -> list[int]:
    """
    Meses do calendário cobertos por inteiro em todos os anos do período.

    Base da comparação entre anos (decisão 0008): com o período de
    janeiro de 2023 a junho de 2026, são os meses de janeiro a junho.
    Início e fim têm como padrão os do config; sem mês comum, a lista vem vazia.
    """
    inicio = inicio or config.PERIODO_INICIO
    fim = fim or config.PERIODO_FIM
    comuns: set[int] | None = None
    for ano in range(inicio.year, fim.year + 1):
        cobertos = {
            mes
            for mes in range(1, 13)
            if date(ano, mes, 1) >= inicio and _ultimo_dia(ano, mes) <= fim
        }
        comuns = cobertos if comuns is None else comuns & cobertos
    return sorted(comuns or set())


def _pessoa_tempo_meses_por_ano(anos: list[int], meses: list[int]) -> dict[int, float]:
    """Pessoas-ano de cada ano contando só os meses dados."""
    return {
        ano: sum(
            pessoa_tempo(config.POPULACAO_ANUAL, date(ano, mes, 1), _ultimo_dia(ano, mes))
            for mes in meses
        )
        for ano in anos
    }


def _anos_parciais() -> set[int]:
    """Anos do período que não vão de 1º de janeiro a 31 de dezembro."""
    inicio, fim = config.PERIODO_INICIO, config.PERIODO_FIM
    return {
        ano
        for ano in range(inicio.year, fim.year + 1)
        if max(inicio, date(ano, 1, 1)) > date(ano, 1, 1)
        or min(fim, date(ano, 12, 31)) < date(ano, 12, 31)
    }


def ultimo_ano_completo() -> int:
    """Último ano civil inteiro dentro do período configurado."""
    fim = config.PERIODO_FIM
    return fim.year if (fim.month, fim.day) == (12, 31) else fim.year - 1


def _wilson_percentual(sucessos: int, total: int, casas: int = 1) -> tuple[float, float]:
    """IC de Wilson em escala 0 a 100."""
    if total <= 0:
        return 0.0, 0.0
    inferior, superior = ic_wilson(int(sucessos), int(total))
    return round(inferior * 100, casas), round(superior * 100, casas)


def _adicionar_wilson(df: pd.DataFrame, coluna_sucessos: str, coluna_total: str) -> pd.DataFrame:
    """Acrescenta colunas ic_inferior e ic_superior (0 a 100) a uma tabela."""
    if df.empty:
        return df.assign(ic_inferior=pd.Series(dtype=float), ic_superior=pd.Series(dtype=float))
    limites = [
        _wilson_percentual(s, n) for s, n in zip(df[coluna_sucessos], df[coluna_total], strict=True)
    ]
    df = df.copy()
    df["ic_inferior"] = [a for a, _ in limites]
    df["ic_superior"] = [b for _, b in limites]
    return df
