"""Notificações do SINAN por agravo e ano, e presença de cada grupo no SINAN e no SIH."""

from dataclasses import dataclass

import pandas as pd

from src import config
from src.estatistica import ic_taxa_por_100mil, taxa_por_100mil

from ._comum import pessoa_ano_periodo


@dataclass(frozen=True)
class CruzamentoFontes:
    """
    Cobertura de um grupo de agravo em cada fonte de dado.

    As fontes não são comparáveis por divisão: o SINAN registra apenas
    agravos de notificação compulsória, enquanto o SIH classifica todas
    as internações por CID-10.
    """

    grupo: str
    notificacoes: int
    internacoes: int
    leitura: str  # em qual fonte o grupo aparece
    casos: int = 0  # decisão 0001: confirmados; sem CLASSI_FIN, as notificações


def _contagens_classificacao(sinan: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """Notificações, confirmados, descartados, sem classificação e outros códigos."""
    rotulos = {
        "confirmados": config.SINAN_CONFIRMADO,
        "descartados": config.SINAN_DESCARTADO,
        "sem_classificacao": config.SINAN_SEM_CLASSIFICACAO,
        "outros_codigos": config.SINAN_OUTRO_CODIGO,
    }
    contagens = sinan.assign(
        **{col: sinan["classificacao"] == rotulo for col, rotulo in rotulos.items()}
    )
    resumo = (
        contagens.groupby(chaves)
        .agg(notificacoes=("classificacao", "size"), **{c: (c, "sum") for c in rotulos})
        .reset_index()
    )
    resumo[list(rotulos)] = resumo[list(rotulos)].astype(int)
    resumo["tem_classi_fin"] = ~resumo["agravo"].isin(config.SINAN_SEM_CLASSI_FIN)
    return resumo


def _casos_sinan(sinan: pd.DataFrame) -> pd.Series:
    """Notificações que contam como caso: confirmadas, ou de agravo sem CLASSI_FIN."""
    return sinan["classificacao"].isin([config.SINAN_CONFIRMADO, config.SINAN_FICHA_SEM_CLASSI])


def perfil_notificacoes(sinan: pd.DataFrame) -> pd.DataFrame:
    """
    Resume o SINAN por agravo no período inteiro, com taxa e IC (decisão 0001).

    O caso é a notificação confirmada. Nos agravos sem CLASSI_FIN
    (config.SINAN_SEM_CLASSI_FIN), o caso é a notificação. A taxa e o IC de
    Garwood usam os casos; o total notificado, os descartados e os sem
    classificação aparecem como contagens. Como sensibilidade, o máximo
    possível soma confirmados e sem classificação, com taxa e IC.

    Taxas por 100 mil pessoas-ano. amostra_suficiente compara os casos com
    config.LIMIAR_AMOSTRA_MINIMA; a_conferir marca o agravo cujo código de
    CLASSI_FIN ainda não foi conferido no dicionário nacional.
    """
    colunas = [
        "grupo_agravo",
        "agravo",
        "notificacoes",
        "confirmados",
        "descartados",
        "sem_classificacao",
        "outros_codigos",
        "tem_classi_fin",
        "casos",
        "taxa_100mil",
        "taxa_ic_inferior",
        "taxa_ic_superior",
        "casos_maximo",
        "taxa_maximo",
        "maximo_ic_inferior",
        "maximo_ic_superior",
        "amostra_suficiente",
        "a_conferir",
    ]
    if sinan.empty:
        return pd.DataFrame(columns=colunas)

    pessoa_ano = pessoa_ano_periodo()
    resumo = _contagens_classificacao(sinan, ["grupo_agravo", "agravo"])

    resumo["casos"] = resumo["confirmados"].where(resumo["tem_classi_fin"], resumo["notificacoes"])
    resumo["casos_maximo"] = (resumo["confirmados"] + resumo["sem_classificacao"]).where(
        resumo["tem_classi_fin"], resumo["notificacoes"]
    )
    for casos, taxa, inferior, superior in (
        ("casos", "taxa_100mil", "taxa_ic_inferior", "taxa_ic_superior"),
        ("casos_maximo", "taxa_maximo", "maximo_ic_inferior", "maximo_ic_superior"),
    ):
        resumo[taxa] = [round(taxa_por_100mil(int(n), pessoa_ano), 2) for n in resumo[casos]]
        limites = [ic_taxa_por_100mil(int(n), pessoa_ano) for n in resumo[casos]]
        resumo[inferior] = [round(a, 2) for a, _ in limites]
        resumo[superior] = [round(b, 2) for _, b in limites]

    resumo["amostra_suficiente"] = resumo["casos"] >= config.LIMIAR_AMOSTRA_MINIMA
    nomes_a_conferir = {config.SINAN_AGRAVOS[s][0] for s in config.SINAN_CLASSI_A_CONFERIR}
    resumo["a_conferir"] = resumo["agravo"].isin(nomes_a_conferir)

    return resumo.sort_values("notificacoes", ascending=False)[colunas]


def notificacoes_por_ano(sinan: pd.DataFrame) -> pd.DataFrame:
    """
    Contagens do SINAN por agravo e ano, sem taxa.

    Com contagens de 0 a poucas unidades por ano, uma taxa anual é instável
    e engana; a taxa fica só no período inteiro (perfil_notificacoes).
    """
    colunas = [
        "grupo_agravo",
        "agravo",
        "ano",
        "notificacoes",
        "confirmados",
        "descartados",
        "sem_classificacao",
        "outros_codigos",
        "tem_classi_fin",
    ]
    if sinan.empty:
        return pd.DataFrame(columns=colunas)
    resumo = _contagens_classificacao(sinan, ["grupo_agravo", "agravo", "ano"])
    resumo["ano"] = resumo["ano"].astype(int)
    return resumo.sort_values(["agravo", "ano"])[colunas].reset_index(drop=True)


def cruzar_notificacoes_internacoes(
    sinan: pd.DataFrame,
    sih: pd.DataFrame,
) -> list[CruzamentoFontes]:
    """
    Presença de cada grupo de agravo no SINAN e no SIH, por internações.

    Não calcula razão entre as fontes: SINAN e SIH captam universos
    distintos. A leitura só descreve em qual fonte o grupo aparece, sem
    afirmar o motivo, que pode ser a regra de notificação, a gravidade
    dos casos ou subnotificação. A leitura usa a presença de notificações;
    casos segue a decisão 0001. Sem a coluna 'classificacao' no SINAN,
    toda notificação conta como caso.
    """
    grupos_sinan = set(sinan["grupo_agravo"].dropna().unique()) if not sinan.empty else set()
    grupos = sorted(grupos_sinan | set(sih["grupo_agravo"].dropna().unique()))
    casos = (
        _casos_sinan(sinan)
        if not sinan.empty and "classificacao" in sinan.columns
        else pd.Series(True, index=sinan.index)
    )

    resultados = []

    for grupo in grupos:
        do_grupo = sinan["grupo_agravo"] == grupo if not sinan.empty else pd.Series(dtype=bool)
        n_sinan = int(do_grupo.sum())
        n_casos = int((do_grupo & casos).sum())
        n_sih = int((sih["grupo_agravo"] == grupo).sum())

        if n_sinan == 0 and n_sih > 0:
            leitura = "registrado apenas no SIH no período"
        elif n_sih == 0 and n_sinan > 0:
            leitura = "registrado apenas no SINAN no período"
        elif n_sinan > 0 and n_sih > 0:
            leitura = "presente nas duas fontes"
        else:
            leitura = "sem registro em nenhuma das fontes"

        resultados.append(
            CruzamentoFontes(
                grupo=grupo,
                notificacoes=n_sinan,
                internacoes=n_sih,
                leitura=leitura,
                casos=n_casos,
            )
        )

    return sorted(resultados, key=lambda r: r.internacoes, reverse=True)
