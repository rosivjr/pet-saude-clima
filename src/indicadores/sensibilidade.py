"""Indicadores principais refeitos sem o ano parcial (decisão 0006)."""

from datetime import date

import pandas as pd

from src import config

from ._comum import ultimo_ano_completo
from .agua import avaliar_conformidade_agua, avaliar_microbiologico
from .internacoes import indicador_drsai, perfil_por_grupo


def _indicadores_principais(
    internacoes: pd.DataFrame, agua: pd.DataFrame, fim: date | None = None
) -> dict:
    """Valores e IC dos indicadores comparados na sensibilidade, até fim."""
    resultado = {}
    drsai = indicador_drsai(internacoes, fim)
    resultado["Taxa de internação DRSAI"] = (
        "/100 mil p-a",
        drsai.taxa_100mil,
        drsai.taxa_ic_inferior,
        drsai.taxa_ic_superior,
    )
    resultado["Letalidade hospitalar DRSAI"] = (
        "%",
        drsai.letalidade,
        drsai.letalidade_ic_inferior,
        drsai.letalidade_ic_superior,
    )
    for p in perfil_por_grupo(internacoes, fim):
        if p.grupo in config.GRUPOS_DRSAI and p.amostra_suficiente:
            resultado[f"Taxa de internação {p.grupo}"] = (
                "/100 mil p-a",
                p.taxa_100mil,
                p.taxa_ic_inferior,
                p.taxa_ic_superior,
            )
    for r in avaliar_conformidade_agua(agua):
        if r.parametro == config.PARAMETRO_CLORO:
            resultado["Cloro abaixo do mínimo"] = (
                "%",
                r.percentual_fora,
                r.ic_inferior,
                r.ic_superior,
            )
    for _, reg in avaliar_microbiologico(agua).iterrows():
        resultado[f"{reg['PARAMETRO']} presente"] = (
            "%",
            reg["percentual_presenca"],
            reg["ic_inferior"],
            reg["ic_superior"],
        )
    return resultado


def sensibilidade_sem_ano_parcial(internacoes: pd.DataFrame, agua: pd.DataFrame) -> pd.DataFrame:
    """
    Recalcula os indicadores principais só com anos completos.

    O último ano do período é parcial e sujeito a atraso de registro. Se o
    resultado mudar pouco sem ele, a conclusão não depende desse ano.
    Recebe o SIH e o SISAGUA do período principal; volta vazio se o período
    já termina em 31 de dezembro.
    """
    colunas = [
        "indicador",
        "unidade",
        "principal",
        "principal_ic_inferior",
        "principal_ic_superior",
        "sensibilidade",
        "sens_ic_inferior",
        "sens_ic_superior",
    ]
    fim_completo = date(ultimo_ano_completo(), 12, 31)
    if fim_completo >= config.PERIODO_FIM:
        return pd.DataFrame(columns=colunas)

    principal = _indicadores_principais(internacoes, agua)
    limite = pd.Timestamp(fim_completo)
    sens = _indicadores_principais(
        internacoes[internacoes["DT_INTER"] <= limite],
        agua[agua["DT_COLETA"] <= limite],
        fim_completo,
    )

    linhas = []
    for nome, (unidade, valor, inf, sup) in principal.items():
        s_valor, s_inf, s_sup = sens.get(nome, (unidade, None, None, None))[1:]
        linhas.append(
            {
                "indicador": nome,
                "unidade": unidade,
                "principal": valor,
                "principal_ic_inferior": inf,
                "principal_ic_superior": sup,
                "sensibilidade": s_valor,
                "sens_ic_inferior": s_inf,
                "sens_ic_superior": s_sup,
            }
        )
    return pd.DataFrame(linhas, columns=colunas)
