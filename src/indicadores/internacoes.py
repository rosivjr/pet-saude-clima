"""Internações por DRSAI no SIH: perfis por grupo, faixa etária e séries mensais e anuais."""

import logging
from dataclasses import dataclass
from datetime import date

import pandas as pd

from src import config
from src.estatistica import (
    ic_taxa_por_100mil,
    pessoa_tempo_por_ano,
    razao_taxas,
    taxa_por_100mil,
)

from ._comum import (
    _adicionar_wilson,
    _anos_parciais,
    _pessoa_tempo_meses_por_ano,
    _wilson_percentual,
    meses_comuns,
    pessoa_ano_periodo,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PerfilAgravo:
    """Perfil de internações de um grupo de agravo no período."""

    grupo: str
    internacoes: int
    taxa_100mil: float  # por 100 mil pessoas-ano
    obitos: int
    letalidade: float  # óbitos / internações, 0 a 100
    permanencia_media: float  # dias
    amostra_suficiente: bool  # internações >= config.LIMIAR_AMOSTRA_MINIMA
    taxa_ic_inferior: float = 0.0  # IC 95% de Garwood
    taxa_ic_superior: float = 0.0
    letalidade_ic_inferior: float = 0.0  # IC 95% de Wilson
    letalidade_ic_superior: float = 0.0


def _montar_perfil(
    nome: str,
    bloco: pd.DataFrame,
    pessoa_ano: float,
) -> PerfilAgravo:
    """PerfilAgravo de um recorte de internações, com taxa, letalidade e seus IC."""
    total = len(bloco)
    obitos = int(bloco["MORTE"].sum())
    permanencia = bloco["DIAS_PERM"].dropna()
    taxa_inf, taxa_sup = ic_taxa_por_100mil(total, pessoa_ano)
    let_inf, let_sup = _wilson_percentual(obitos, total)

    return PerfilAgravo(
        grupo=nome,
        internacoes=total,
        taxa_100mil=round(taxa_por_100mil(total, pessoa_ano), 2),
        taxa_ic_inferior=round(taxa_inf, 2),
        taxa_ic_superior=round(taxa_sup, 2),
        obitos=obitos,
        letalidade=round(obitos / total * 100, 1) if total else 0.0,
        letalidade_ic_inferior=let_inf,
        letalidade_ic_superior=let_sup,
        permanencia_media=round(permanencia.mean(), 1) if not permanencia.empty else 0.0,
        amostra_suficiente=total >= config.LIMIAR_AMOSTRA_MINIMA,
    )


def perfil_por_grupo(df: pd.DataFrame, fim: date | None = None) -> list[PerfilAgravo]:
    """
    Perfil de cada grupo de agravo, do maior para o menor número de internações.

    fim é o fim do período do denominador (padrão: config.PERIODO_FIM).
    """
    pessoa_ano = pessoa_ano_periodo(fim)
    perfis = [
        _montar_perfil(str(grupo), bloco, pessoa_ano)
        for grupo, bloco in df.groupby("grupo_agravo", observed=True)
    ]
    return sorted(perfis, key=lambda p: p.internacoes, reverse=True)


def indicador_drsai(df: pd.DataFrame, fim: date | None = None) -> PerfilAgravo:
    """
    Indicador agregado de internações por DRSAI.

    Mesma definição do indicador do IBGE (internações por DRSAI por local
    de residência / população residente x 100 mil), com pessoa-tempo no
    denominador porque o período não é de um ano. fim é o fim do período
    do denominador (padrão: config.PERIODO_FIM).
    """
    drsai = df[df["grupo_agravo"].isin(config.GRUPOS_DRSAI)]
    return _montar_perfil(config.ROTULO_DRSAI, drsai, pessoa_ano_periodo(fim))


def perfil_etario(
    df: pd.DataFrame,
    grupos: tuple[str, ...] | None = None,
) -> tuple[pd.DataFrame, int]:
    """
    Distribuição por faixa etária, com IC de Wilson do percentual, e número
    de internações sem idade válida.

    Menores de 1 ano (idade em dias ou meses) já entram na faixa '<1'.
    Ficam de fora só os registros sem idade válida. Sem grupos, usa os DRSAI.
    """
    if grupos is None:
        grupos = config.GRUPOS_DRSAI

    do_grupo = df[df["grupo_agravo"].isin(grupos)]
    recorte = do_grupo[do_grupo["faixa_etaria"].notna()]
    excluidos = len(do_grupo) - len(recorte)

    if excluidos:
        logger.warning("%d internações sem idade válida", excluidos)

    if recorte.empty:
        return (
            pd.DataFrame(
                columns=["faixa_etaria", "internacoes", "percentual", "ic_inferior", "ic_superior"]
            ),
            excluidos,
        )

    resumo = (
        recorte["faixa_etaria"]
        .value_counts()
        .sort_index()
        .rename_axis("faixa_etaria")
        .reset_index(name="internacoes")
    )

    total = resumo["internacoes"].sum()
    resumo["percentual"] = (resumo["internacoes"] / total * 100).round(1)
    limites = [_wilson_percentual(n, total) for n in resumo["internacoes"]]
    resumo["ic_inferior"] = [a for a, _ in limites]
    resumo["ic_superior"] = [b for _, b in limites]

    return resumo, excluidos


def perfil_etario_feco_oral(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """perfil_etario restrito ao grupo feco-oral."""
    return perfil_etario(df, grupos=(config.GRUPO_FECO_ORAL,))


def serie_mensal_internacoes(
    df: pd.DataFrame,
    grupos: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Internações por ano e mês dos grupos dados (padrão: os grupos DRSAI)."""
    if grupos is None:
        grupos = config.GRUPOS_DRSAI

    recorte = df[df["grupo_agravo"].isin(grupos)]

    if recorte.empty:
        logger.warning("Sem internações para a série mensal")
        return pd.DataFrame(columns=["ano", "mes", "internacoes"])

    return recorte.groupby(["ano", "mes"], observed=True).size().reset_index(name="internacoes")


def serie_anual_internacoes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Taxa anual de internação por grupo, com IC e razão de taxas.

    Cada ano usa a própria pessoa-tempo. Um ano parcial (2026) entra com a
    fração coberta e fica marcado em ano_parcial; essa taxa anualizada é só
    descrição. A comparação entre anos usa os meses comuns a todos os anos
    (decisão 0008): taxa_mc e a razão de taxas contra o primeiro ano são
    calculadas só nesses meses.

    Entram o agregado DRSAI e os grupos DRSAI com pelo menos
    config.LIMIAR_AMOSTRA_MINIMA internações no período. As colunas com
    sufixo _mc são as medidas nos meses comuns.
    """
    colunas = [
        "indicador",
        "ano",
        "ano_parcial",
        "internacoes",
        "pessoa_ano",
        "taxa",
        "taxa_ic_inferior",
        "taxa_ic_superior",
        "internacoes_mc",
        "pessoa_ano_mc",
        "taxa_mc",
        "taxa_mc_ic_inferior",
        "taxa_mc_ic_superior",
        "razao_taxas",
        "rt_ic_inferior",
        "rt_ic_superior",
    ]
    pa_por_ano = pessoa_tempo_por_ano(
        config.POPULACAO_ANUAL, config.PERIODO_INICIO, config.PERIODO_FIM
    )
    anos = sorted(pa_por_ano)
    primeiro = anos[0]
    parciais = _anos_parciais()
    meses = meses_comuns()
    pa_mc = _pessoa_tempo_meses_por_ano(anos, meses)

    drsai = df[df["grupo_agravo"].isin(config.GRUPOS_DRSAI)]
    blocos = {config.ROTULO_DRSAI: drsai}
    for grupo in config.GRUPOS_DRSAI:
        bloco = drsai[drsai["grupo_agravo"] == grupo]
        if len(bloco) >= config.LIMIAR_AMOSTRA_MINIMA:
            blocos[grupo] = bloco

    linhas = []
    for indicador, bloco in blocos.items():
        contagem = bloco["ano"].value_counts()
        contagem_mc = bloco.loc[bloco["mes"].isin(meses), "ano"].value_counts()
        base = int(contagem_mc.get(primeiro, 0))

        for ano in anos:
            n = int(contagem.get(ano, 0))
            pa = pa_por_ano[ano]
            inf, sup = ic_taxa_por_100mil(n, pa)
            n_mc = int(contagem_mc.get(ano, 0))
            mc_inf, mc_sup = ic_taxa_por_100mil(n_mc, pa_mc[ano])
            # O ano de referência não tem RT: comparar consigo mesmo não informa.
            rt = (
                None
                if ano == primeiro or not meses
                else razao_taxas(base, pa_mc[primeiro], n_mc, pa_mc[ano])
            )

            linhas.append(
                {
                    "indicador": indicador,
                    "ano": ano,
                    "ano_parcial": ano in parciais,
                    "internacoes": n,
                    "pessoa_ano": round(pa),
                    "taxa": round(taxa_por_100mil(n, pa), 2),
                    "taxa_ic_inferior": round(inf, 2),
                    "taxa_ic_superior": round(sup, 2),
                    "internacoes_mc": n_mc,
                    "pessoa_ano_mc": round(pa_mc[ano]),
                    "taxa_mc": round(taxa_por_100mil(n_mc, pa_mc[ano]), 2) if meses else 0.0,
                    "taxa_mc_ic_inferior": round(mc_inf, 2),
                    "taxa_mc_ic_superior": round(mc_sup, 2),
                    "razao_taxas": round(rt[0], 2) if rt else None,
                    "rt_ic_inferior": round(rt[1], 2) if rt else None,
                    "rt_ic_superior": round(rt[2], 2) if rt else None,
                }
            )

    serie = pd.DataFrame(linhas, columns=colunas)
    serie.attrs["meses_comuns"] = meses
    return serie


def serie_anual_todas_causas(
    todas: pd.DataFrame,
    internacoes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Internações de residentes por todas as causas e a fração que é DRSAI.

    Serve para separar variação do agravo de variação do registro: se o
    total de internações sobe junto, parte do aumento das DRSAI acompanha
    o volume geral; se a proporção DRSAI/total sobe, o aumento é do grupo.
    Como em serie_anual_internacoes, a razão de taxas usa só os meses
    comuns a todos os anos (decisão 0008).

    todas é o SIH de residentes no período, todas as causas (AIH tipo 1);
    internacoes, o SIH já filtrado nos grupos de agravo. A proporção
    DRSAI/total leva IC de Wilson.
    """
    colunas = [
        "ano",
        "ano_parcial",
        "total",
        "pessoa_ano",
        "taxa",
        "taxa_ic_inferior",
        "taxa_ic_superior",
        "total_mc",
        "razao_taxas",
        "rt_ic_inferior",
        "rt_ic_superior",
        "drsai",
        "proporcao_drsai",
        "prop_ic_inferior",
        "prop_ic_superior",
    ]
    pa_por_ano = pessoa_tempo_por_ano(
        config.POPULACAO_ANUAL, config.PERIODO_INICIO, config.PERIODO_FIM
    )
    anos = sorted(pa_por_ano)
    primeiro = anos[0]
    parciais = _anos_parciais()
    meses = meses_comuns()
    pa_mc = _pessoa_tempo_meses_por_ano(anos, meses)

    total_ano = todas["ano"].value_counts()
    total_mc_ano = todas.loc[todas["mes"].isin(meses), "ano"].value_counts()
    drsai_ano = internacoes.loc[
        internacoes["grupo_agravo"].isin(config.GRUPOS_DRSAI), "ano"
    ].value_counts()
    base = int(total_mc_ano.get(primeiro, 0))

    linhas = []
    for ano in anos:
        n = int(total_ano.get(ano, 0))
        n_mc = int(total_mc_ano.get(ano, 0))
        d = int(drsai_ano.get(ano, 0))
        pa = pa_por_ano[ano]
        inf, sup = ic_taxa_por_100mil(n, pa)
        rt = (
            None
            if ano == primeiro or not meses
            else razao_taxas(base, pa_mc[primeiro], n_mc, pa_mc[ano])
        )
        p_inf, p_sup = _wilson_percentual(d, n, casas=2)

        linhas.append(
            {
                "ano": ano,
                "ano_parcial": ano in parciais,
                "total": n,
                "pessoa_ano": round(pa),
                "taxa": round(taxa_por_100mil(n, pa), 1),
                "taxa_ic_inferior": round(inf, 1),
                "taxa_ic_superior": round(sup, 1),
                "total_mc": n_mc,
                "razao_taxas": round(rt[0], 2) if rt else None,
                "rt_ic_inferior": round(rt[1], 2) if rt else None,
                "rt_ic_superior": round(rt[2], 2) if rt else None,
                "drsai": d,
                "proporcao_drsai": round(d / n * 100, 2) if n else 0.0,
                "prop_ic_inferior": p_inf,
                "prop_ic_superior": p_sup,
            }
        )

    serie = pd.DataFrame(linhas, columns=colunas)
    serie.attrs["meses_comuns"] = meses
    return serie


def residentes_fora_do_para() -> pd.DataFrame:
    """
    Internações de residentes em hospitais de outras UFs, que o relatório não lê.

    Contagens medidas à parte (config.SIH_RESIDENTES_FORA_DO_PARA), com IC de
    Wilson do percentual (ic_inferior e ic_superior, 0 a 100).
    """
    tabela = pd.DataFrame(
        [
            {"ano": ano, "fora": fora, "total": total, "percentual": round(100 * fora / total, 1)}
            for ano, (fora, total) in config.SIH_RESIDENTES_FORA_DO_PARA.items()
        ],
        columns=["ano", "fora", "total", "percentual"],
    )
    return _adicionar_wilson(tabela, "fora", "total")
