"""
Funções estatísticas dos indicadores.

Cada função é conferida em tests/test_estatistica.py com valores
calculados à mão.
"""

from __future__ import annotations

import math
from datetime import date, datetime

from scipy.stats import chi2

# Quantil 97,5% da normal padrão (IC de 95%).
Z_95 = 1.959963984540054


def _como_data(valor: date | datetime) -> date:
    """Converte datetime ou pandas.Timestamp em date, para comparar datas."""
    return valor.date() if isinstance(valor, datetime) else valor


def pessoa_tempo(
    pop_anual: dict[int, int | None],
    inicio: date | datetime,
    fim: date | datetime,
) -> float:
    """
    Calcula pessoas-ano de observação entre duas datas, inclusive.

    Cada ano contribui com sua população multiplicada pela fração do ano
    coberta pelo período. Usada no denominador quando o período não é de
    exatamente um ano. A população de cada ano vem de config.POPULACAO_ANUAL.

    Raises:
        ValueError: se fim < inicio ou se alguma população não for positiva.
        KeyError: se faltar a população de algum ano do período.
    """
    inicio, fim = _como_data(inicio), _como_data(fim)
    if fim < inicio:
        raise ValueError(f"Período inválido: {inicio} a {fim}")

    total = 0.0
    for ano in range(inicio.year, fim.year + 1):
        pop = pop_anual.get(ano)
        if pop is None:
            raise KeyError(f"População de {ano} ausente em config.POPULACAO_ANUAL")
        if pop <= 0:
            raise ValueError(f"População de {ano} deve ser positiva: {pop}")

        ini_ano, fim_ano = date(ano, 1, 1), date(ano, 12, 31)
        dias_ano = (fim_ano - ini_ano).days + 1
        dias_obs = (min(fim, fim_ano) - max(inicio, ini_ano)).days + 1
        total += pop * dias_obs / dias_ano

    return total


def taxa_por_100mil(casos: int, pessoa_ano: float) -> float:
    """
    Taxa por 100 mil pessoas-ano, sem arredondar.

    O arredondamento fica na camada de apresentação.

    Raises:
        ValueError: se casos < 0 ou pessoa_ano <= 0.
    """
    if casos < 0:
        raise ValueError(f"Casos não pode ser negativo: {casos}")
    if pessoa_ano <= 0:
        raise ValueError(f"Pessoa-tempo deve ser positiva: {pessoa_ano}")
    return casos / pessoa_ano * 100_000


def ic_garwood(casos: int, alfa: float = 0.05) -> tuple[float, float]:
    """
    Intervalo de confiança exato de Poisson (Garwood) para uma contagem.

    Limite inferior: chi2(alfa/2; 2k) / 2, igual a 0 quando k = 0.
    Limite superior: chi2(1 - alfa/2; 2k + 2) / 2.

    Args:
        casos: contagem observada (inteiro >= 0).
        alfa: nível de significância (0,05 gera IC de 95%).

    Returns:
        Tupla (inferior, superior) em número de casos.
    """
    if casos < 0 or int(casos) != casos:
        raise ValueError(f"Contagem deve ser inteiro >= 0: {casos}")
    inferior = chi2.ppf(alfa / 2, 2 * casos) / 2 if casos > 0 else 0.0
    superior = chi2.ppf(1 - alfa / 2, 2 * casos + 2) / 2
    return float(inferior), float(superior)


def ic_taxa_por_100mil(
    casos: int,
    pessoa_ano: float,
    alfa: float = 0.05,
) -> tuple[float, float]:
    """IC de Garwood convertido para taxa por 100 mil pessoas-ano."""
    if pessoa_ano <= 0:
        raise ValueError(f"Pessoa-tempo deve ser positiva: {pessoa_ano}")
    inferior, superior = ic_garwood(casos, alfa)
    return inferior / pessoa_ano * 100_000, superior / pessoa_ano * 100_000


def ic_wilson(sucessos: int, total: int, z: float = Z_95) -> tuple[float, float]:
    """
    Intervalo de Wilson para uma proporção, em escala 0 a 1.

    Usado em letalidade e em percentual de amostras fora do padrão, onde o
    IC de Wald falha com proporções próximas de 0 ou 1.

    Raises:
        ValueError: se total <= 0 ou sucessos fora de [0, total].
    """
    if total <= 0:
        raise ValueError(f"Total deve ser positivo: {total}")
    if not 0 <= sucessos <= total:
        raise ValueError(f"Sucessos fora de [0, {total}]: {sucessos}")

    p = sucessos / total
    z2 = z * z
    denominador = 1 + z2 / total
    centro = (p + z2 / (2 * total)) / denominador
    margem = z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / denominador
    return max(0.0, centro - margem), min(1.0, centro + margem)


def pessoa_tempo_por_ano(
    pop_anual: dict[int, int | None],
    inicio: date | datetime,
    fim: date | datetime,
) -> dict[int, float]:
    """
    Pessoas-ano de cada ano civil dentro do período.

    Usada na taxa anualizada de cada ano, que é só descritiva: um ano
    parcial (ex.: jan-jun de 2026) entra com a fração coberta. A comparação
    entre anos não usa esta função, e sim os meses comuns a todos os anos
    (meses_comuns, decisão 0008).
    """
    inicio, fim = _como_data(inicio), _como_data(fim)
    return {
        ano: pessoa_tempo(pop_anual, max(inicio, date(ano, 1, 1)), min(fim, date(ano, 12, 31)))
        for ano in range(inicio.year, fim.year + 1)
    }


def razao_taxas(
    casos_a: int,
    pessoa_ano_a: float,
    casos_b: int,
    pessoa_ano_b: float,
    z: float = Z_95,
) -> tuple[float, float, float] | None:
    """
    Razão de taxas (b / a) com IC pela aproximação do logaritmo.

    IC = exp(ln(RT) +/- z * raiz(1/casos_a + 1/casos_b)).

    Returns:
        Tupla (razão, inferior, superior), ou None se alguma contagem for
        zero, caso em que a razão não é estimável por este método.
    """
    if casos_a <= 0 or casos_b <= 0:
        return None
    if pessoa_ano_a <= 0 or pessoa_ano_b <= 0:
        raise ValueError("Pessoa-tempo deve ser positiva")

    razao = (casos_b / pessoa_ano_b) / (casos_a / pessoa_ano_a)
    erro = math.sqrt(1 / casos_a + 1 / casos_b)
    return (
        razao,
        math.exp(math.log(razao) - z * erro),
        math.exp(math.log(razao) + z * erro),
    )
