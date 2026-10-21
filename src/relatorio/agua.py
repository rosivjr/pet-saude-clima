"""Seções de qualidade da água do SISAGUA: conformidade, microbiologia e séries."""

import pandas as pd

from src import config
from src.indicadores import ResultadoConformidade

from ._formato import ic, numero, subtitulo, titulo


def _limite_legal(r: ResultadoConformidade) -> str:
    """Limite da Portaria 888/2021 em texto: 'mínimo 0,2 mg/L', 'entre 6,0 e 9,5'."""
    unidade = f" {r.unidade}" if r.unidade else ""
    if r.limite_minimo is not None and r.limite_maximo is not None:
        return f"entre {numero(r.limite_minimo)} e {numero(r.limite_maximo)}{unidade}"
    if r.limite_minimo is not None:
        return f"mínimo {numero(r.limite_minimo)}{unidade}"
    return f"máximo {numero(r.limite_maximo)}{unidade}"


def secao_conformidade(resultados: list[ResultadoConformidade]) -> str:
    """Formata a seção de conformidade físico-química da água."""
    linhas = [titulo("8. QUALIDADE DA ÁGUA — PARÂMETROS FÍSICO-QUÍMICOS")]
    linhas.append(f"Critério: {config.CRITERIO_PORTARIA_888}\n")

    for r in resultados:
        linhas.append(
            f"  {r.parametro}\n"
            f"    Limite legal .......... {_limite_legal(r)}\n"
            f"    Amostras .............. {r.total_amostras}\n"
            f"    Fora do padrão ........ {r.fora_do_padrao} "
            f"({numero(r.percentual_fora)}%, {ic(r.ic_inferior, r.ic_superior)})\n"
        )

    return "\n".join(linhas)


def secao_microbiologica(resumo: pd.DataFrame) -> str:
    """Formata a seção de parâmetros microbiológicos da água."""
    linhas = [titulo("9. QUALIDADE DA ÁGUA — PARÂMETROS MICROBIOLÓGICOS")]
    linhas.append(
        "Indicador: percentual de amostras com presença. A Portaria 888/2021\n"
        "(Anexo 1) avalia coliformes totais no conjunto mensal de amostras do\n"
        "responsável pelo sistema; as amostras do SISAGUA aqui são da vigilância.\n"
        "E. coli: ausência em 100 mL.\n"
    )

    for _, linha in resumo.iterrows():
        linhas.append(
            f"  {linha['PARAMETRO']}\n"
            f"    Amostras .............. {linha['total']}\n"
            f"    Presentes ............. {linha['presentes']} "
            f"({numero(linha['percentual_presenca'])}%, "
            f"{ic(linha['ic_inferior'], linha['ic_superior'])})\n"
        )

    return "\n".join(linhas)


def secao_serie_agua(serie: pd.DataFrame, parametro: str) -> str:
    """Formata a série mensal de um parâmetro da água."""
    linhas = [titulo(f"10. SÉRIE MENSAL — {parametro.upper()}")]

    if serie.empty:
        linhas.append("  Sem dados disponíveis.\n")
        return "\n".join(linhas)

    linhas.append(f"  {'Ano':<8}{'Mês':<8}{'Amostras':>12}{'Média':>12}{'Mediana':>12}")
    linhas.append(f"  {'-' * 52}")

    for _, reg in serie.iterrows():
        linhas.append(
            f"  {int(reg['ano']):<8}{config.MESES_ABREV[int(reg['mes'])]:<8}"
            f"{int(reg['amostras']):>12}"
            f"{numero(reg['media'], 3):>12}{numero(reg['mediana'], 3):>12}"
        )

    return "\n".join(linhas) + "\n"


def secao_serie_anual_agua(serie: pd.DataFrame) -> str:
    """Formata a proporção anual de amostras fora do padrão ou com presença, com IC."""
    linhas = [titulo("17. SÉRIE ANUAL — QUALIDADE DA ÁGUA")]

    if serie.empty:
        linhas.append("  Dados insuficientes.\n")
        return "\n".join(linhas)

    linhas.append(
        "O número de amostras varia entre anos; percentuais com poucas\n"
        "amostras têm intervalo largo e devem ser lidos com cautela.\n"
    )

    for indicador, bloco in serie.groupby("indicador", sort=False):
        linhas.append(subtitulo(str(indicador)))
        linhas.append(
            f"  {'Ano':<6}{'Amostras':>10}{'Fora do padrão ou com presença':>32}{'%':>8}  IC95%"
        )
        for _, reg in bloco.iterrows():
            linhas.append(
                f"  {int(reg['ano']):<6}{int(reg['amostras']):>10}{int(reg['fora']):>32}"
                f"{numero(reg['percentual']) + '%':>8}  "
                f"{numero(reg['ic_inferior'])}–{numero(reg['ic_superior'])}%"
            )

    return "\n".join(linhas) + "\n"
