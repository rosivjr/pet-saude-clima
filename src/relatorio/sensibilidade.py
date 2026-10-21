"""Seção da análise de sensibilidade sem o ano parcial (decisão 0006)."""

import pandas as pd

from src import config
from src.indicadores import ultimo_ano_completo

from ._formato import data, numero, titulo


def _valor_com_ic(valor, inferior, superior, casas: int) -> str:
    """Valor com o intervalo de confiança entre parênteses; '—' se ausente."""
    if valor is None or pd.isna(valor):
        return "—"
    return f"{numero(valor, casas)} ({numero(inferior, casas)}–{numero(superior, casas)})"


def secao_sensibilidade(sens: pd.DataFrame) -> str:
    """Formata a comparação dos indicadores com e sem o ano parcial."""
    linhas = [titulo("24. ANÁLISE DE SENSIBILIDADE — SEM O ANO PARCIAL")]
    if sens.empty:
        linhas.append("  O período termina em ano completo; não se aplica.\n")
        return "\n".join(linhas)

    linhas.append(
        f"Principal: {data(config.PERIODO_INICIO)} a {data(config.PERIODO_FIM)}. "
        f"Sensibilidade: até 31/12/{ultimo_ano_completo()}.\n"
        "O último ano do período é parcial e sujeito a atraso de registro.\n"
    )
    linhas.append(f"  {'Indicador':<40}{'Principal':>22}{'Só anos completos':>24}")
    for _, reg in sens.iterrows():
        casas = 2 if reg["unidade"].startswith("/") else 1
        principal = _valor_com_ic(
            reg["principal"], reg["principal_ic_inferior"], reg["principal_ic_superior"], casas
        )
        sensibilidade = _valor_com_ic(
            reg["sensibilidade"], reg["sens_ic_inferior"], reg["sens_ic_superior"], casas
        )
        linhas.append(f"  {str(reg['indicador'])[:39]:<40}{principal:>22}{sensibilidade:>24}")
    linhas.append(
        "\n  Taxas por 100 mil pessoas-ano; percentuais com IC de Wilson.\n"
        "  A comparação é descritiva: mostra quanto o valor muda sem o ano\n"
        "  parcial. Sobreposição de intervalos não é teste formal de diferença."
    )
    return "\n".join(linhas) + "\n"
