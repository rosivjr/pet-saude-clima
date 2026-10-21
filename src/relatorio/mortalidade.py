"""Seção de óbitos do SIM por grupo de agravo, ano e faixa etária."""

import pandas as pd

from src import config

from ._formato import numero, subtitulo, titulo


def secao_mortalidade(
    por_grupo: pd.DataFrame,
    serie: pd.DataFrame,
    por_faixa: pd.DataFrame,
    anos: list[int],
) -> str:
    """Formata os óbitos por DRSAI do SIM; anos são os que têm arquivo do SIM carregado."""
    linhas = [titulo("22. MORTALIDADE POR DRSAI (SIM)")]
    if not anos:
        linhas.append("  Nenhum ano do SIM disponível nesta execução.\n")
        return "\n".join(linhas)

    faltam = [
        a for a in range(config.PERIODO_INICIO.year, config.PERIODO_FIM.year + 1) if a not in anos
    ]
    linhas.append(
        "Fonte: SIM/DATASUS, Declaração de Óbito, causa básica, residentes.\n"
        f"Anos com arquivo carregado: {', '.join(str(a) for a in anos)}.\n"
        + (
            f"Sem arquivo carregado: {', '.join(str(a) for a in faltam)}; "
            "esses anos não entram\nno numerador nem no denominador.\n"
            if faltam
            else ""
        )
        + "Taxa por 100 mil pessoas-ano dos anos carregados, com IC de Garwood.\n"
    )

    linhas.append(subtitulo("Óbitos por grupo (causa básica)"))
    linhas.append(f"  {'Grupo':<30}{'Óbitos':>8}{'Taxa':>9}  IC95%")
    for _, reg in por_grupo.iterrows():
        marca = "  [!]" if 0 < reg["obitos"] < config.LIMIAR_AMOSTRA_MINIMA else ""
        linhas.append(
            f"  {str(reg['grupo'])[:29]:<30}{int(reg['obitos']):>8}"
            f"{numero(reg['taxa_100mil'], 2):>9}  "
            f"{numero(reg['taxa_ic_inferior'], 2)}–{numero(reg['taxa_ic_superior'], 2)}{marca}"
        )

    linhas.append(subtitulo("Por ano"))
    linhas.append(
        f"  {'Ano':<6}{'Todas causas':>13}{'DRSAI':>7}{'Taxa DRSAI':>12}  "
        f"{'IC95%':<13}{'DRSAI/total % (IC 95%)':>23}"
    )
    for _, reg in serie.iterrows():
        proporcao = (
            f"{numero(reg['proporcao_drsai'], 2)}% "
            f"({numero(reg['proporcao_ic_inferior'], 2)}–{numero(reg['proporcao_ic_superior'], 2)})"
        )
        linhas.append(
            f"  {int(reg['ano']):<6}{int(reg['obitos_total']):>13}{int(reg['obitos_drsai']):>7}"
            f"{numero(reg['taxa_drsai'], 2):>12}  "
            f"{numero(reg['taxa_ic_inferior'], 2) + '–' + numero(reg['taxa_ic_superior'], 2):<13}"
            f"{proporcao:>23}"
        )

    if not por_faixa.empty:
        linhas.append(subtitulo("Óbitos por DRSAI por faixa etária"))
        linhas.append(f"  {'Faixa':<10}{'Óbitos':>6}{'%':>9}  IC95%")
        for _, reg in por_faixa.iterrows():
            linhas.append(
                f"  {str(reg['faixa_etaria']):<10}{int(reg['obitos']):>6}"
                f"{numero(reg['percentual']) + '%':>9}  "
                f"{numero(reg['ic_inferior'])}–{numero(reg['ic_superior'])}%"
            )

    linhas.append(
        "\n  Óbitos por DRSAI são eventos raros. "
        f"[!] menos de {config.LIMIAR_AMOSTRA_MINIMA} casos:\n"
        "  estimativa instável. O SIM do ano mais recente\n"
        "  costuma ser preliminar e pode mudar após a consolidação."
    )
    return "\n".join(linhas) + "\n"
