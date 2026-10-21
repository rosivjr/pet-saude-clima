"""Óbitos do SIM por grupo de agravo, ano e faixa etária."""

import pandas as pd

from src import config
from src.estatistica import ic_taxa_por_100mil, pessoa_tempo_por_ano, taxa_por_100mil

from ._comum import _wilson_percentual


def pessoa_ano_anos(anos: list[int]) -> dict[int, float]:
    """Pessoas-ano de cada ano da lista, recortado ao período configurado."""
    pa = pessoa_tempo_por_ano(config.POPULACAO_ANUAL, config.PERIODO_INICIO, config.PERIODO_FIM)
    return {ano: pa[ano] for ano in anos if ano in pa}


def mortalidade_por_grupo(obitos: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """
    Óbitos por causa básica em cada grupo de agravo, com taxa e IC.

    O denominador usa só a pessoa-tempo dos anos com arquivo do SIM
    carregado (anos): um ano sem dado não pode entrar no denominador. O
    agregado DRSAI vem na primeira linha.
    """
    colunas = ["grupo", "obitos", "taxa_100mil", "taxa_ic_inferior", "taxa_ic_superior"]
    pa = sum(pessoa_ano_anos(anos).values())
    if not pa:
        return pd.DataFrame(columns=colunas)

    classificados = obitos[obitos["grupo_agravo"].notna()] if not obitos.empty else obitos
    blocos = {
        config.ROTULO_DRSAI: classificados[classificados["grupo_agravo"].isin(config.GRUPOS_DRSAI)]
        if not classificados.empty
        else classificados
    }
    for grupo in config.GRUPOS_AGRAVO:
        blocos[grupo] = (
            classificados[classificados["grupo_agravo"] == grupo]
            if not classificados.empty
            else classificados
        )

    linhas = []
    for grupo, bloco in blocos.items():
        n = len(bloco)
        inf, sup = ic_taxa_por_100mil(n, pa)
        linhas.append(
            {
                "grupo": grupo,
                "obitos": n,
                "taxa_100mil": round(taxa_por_100mil(n, pa), 2),
                "taxa_ic_inferior": round(inf, 2),
                "taxa_ic_superior": round(sup, 2),
            }
        )
    return pd.DataFrame(linhas, columns=colunas)


def serie_anual_mortalidade(obitos: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Óbitos por DRSAI e por todas as causas, taxa DRSAI e proporção com IC, por ano com SIM."""
    colunas = [
        "ano",
        "obitos_total",
        "obitos_drsai",
        "taxa_drsai",
        "taxa_ic_inferior",
        "taxa_ic_superior",
        "proporcao_drsai",
        "proporcao_ic_inferior",
        "proporcao_ic_superior",
    ]
    pa = pessoa_ano_anos(anos)
    linhas = []
    for ano in sorted(pa):
        do_ano = obitos[obitos["ano"] == ano] if not obitos.empty else obitos
        total = len(do_ano)
        drsai = int(do_ano["grupo_agravo"].isin(config.GRUPOS_DRSAI).sum()) if total else 0
        inf, sup = ic_taxa_por_100mil(drsai, pa[ano])
        prop_inf, prop_sup = _wilson_percentual(drsai, total, casas=2)
        linhas.append(
            {
                "ano": ano,
                "obitos_total": total,
                "obitos_drsai": drsai,
                "taxa_drsai": round(taxa_por_100mil(drsai, pa[ano]), 2),
                "taxa_ic_inferior": round(inf, 2),
                "taxa_ic_superior": round(sup, 2),
                "proporcao_drsai": round(drsai / total * 100, 2) if total else 0.0,
                "proporcao_ic_inferior": prop_inf,
                "proporcao_ic_superior": prop_sup,
            }
        )
    return pd.DataFrame(linhas, columns=colunas)


def mortalidade_por_faixa(obitos: pd.DataFrame) -> pd.DataFrame:
    """Óbitos por DRSAI por faixa etária (contagem e percentual, com IC de Wilson)."""
    colunas = ["faixa_etaria", "obitos", "percentual", "ic_inferior", "ic_superior"]
    if obitos.empty:
        return pd.DataFrame(columns=colunas)
    drsai = obitos[
        obitos["grupo_agravo"].isin(config.GRUPOS_DRSAI) & obitos["faixa_etaria"].notna()
    ]
    if drsai.empty:
        return pd.DataFrame(columns=colunas)
    resumo = (
        drsai["faixa_etaria"]
        .value_counts()
        .sort_index()
        .rename_axis("faixa_etaria")
        .reset_index(name="obitos")
    )
    resumo = resumo[resumo["obitos"] > 0]
    total = resumo["obitos"].sum()
    resumo["percentual"] = (resumo["obitos"] / total * 100).round(1)
    limites = [_wilson_percentual(n, total) for n in resumo["obitos"]]
    resumo["ic_inferior"] = [a for a, _ in limites]
    resumo["ic_superior"] = [b for _, b in limites]
    return resumo
