"""Rede de estabelecimentos de saúde do CNES e local das internações dos residentes."""

import logging
from dataclasses import dataclass

import pandas as pd

from src import config

from ._comum import _wilson_percentual

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PerfilRede:
    """Rede de saúde do município; tipos, leitos e urgência contam só estabelecimentos SUS."""

    total: int
    vinculados_sus: int
    por_tipo_sus: dict[str, int]
    com_leitos: int  # estabelecimentos SUS com leitos hospitalares
    com_urgencia: int
    # Sem IC: o cadastro do CNES é contagem completa, não amostra (docs/metodos.md).
    percentual_sus: float = 0.0
    percentual_sem_sus: float = 0.0


def rede_do_ano(rede: pd.DataFrame, ano: int | None = None) -> pd.DataFrame:
    """Estabelecimentos de uma competência (padrão: a mais recente carregada)."""
    if rede.empty:
        return rede
    ano = ano or int(rede["competencia_ano"].max())
    return rede[rede["competencia_ano"] == ano]


def serie_rede_por_ano(rede: pd.DataFrame) -> pd.DataFrame:
    """Composição da rede em cada competência carregada (coluna competencia_ano)."""
    colunas = [
        "ano",
        "estabelecimentos",
        "vinculo_sus",
        "hospitais_gerais_sus",
        "leitos_hospitais_gerais_sus",
        "sus_com_urgencia",
    ]
    if rede.empty:
        return pd.DataFrame(columns=colunas)

    linhas = []
    for ano, bloco in rede.groupby("competencia_ano"):
        sus = bloco[bloco["VINC_SUS"]]
        hospitais = sus[sus["TP_UNID"] == "05"]
        leitos = sum(
            pd.to_numeric(hospitais[c], errors="coerce").fillna(0).sum()
            for c in ("QTLEITP1", "QTLEITP2", "QTLEITP3")
        )
        linhas.append(
            {
                "ano": int(ano),
                "estabelecimentos": len(bloco),
                "vinculo_sus": len(sus),
                "hospitais_gerais_sus": len(hospitais),
                "leitos_hospitais_gerais_sus": int(leitos),
                "sus_com_urgencia": int(sus["URGEMERG"].sum()),
            }
        )
    return pd.DataFrame(linhas, columns=colunas)


def perfil_rede(df: pd.DataFrame) -> PerfilRede:
    """Composição da rede de estabelecimentos de saúde do município."""
    if df.empty:
        return PerfilRede(0, 0, {}, 0, 0)

    sus = df[df["VINC_SUS"]]

    return PerfilRede(
        total=len(df),
        vinculados_sus=len(sus),
        por_tipo_sus=sus["tipo_unidade"].value_counts().to_dict(),
        com_leitos=int(sus["LEITHOSP"].sum()),
        com_urgencia=int(sus["URGEMERG"].sum()),
        percentual_sus=round(len(sus) / len(df) * 100, 1),
        percentual_sem_sus=round((len(df) - len(sus)) / len(df) * 100, 1),
    )


def local_de_internacao(
    internacoes: pd.DataFrame,
    cnes_municipio: pd.DataFrame,
) -> dict:
    """
    Onde os residentes foram internados, só nos agravos analisados.

    Os leitos do principal estabelecimento vêm da competência mais recente.
    """
    if internacoes.empty or cnes_municipio.empty:
        logger.warning("Dados insuficientes para avaliar local de internação")
        return {}

    do_municipio = set(cnes_municipio["CNES"])
    codigos = internacoes["CNES"].astype(str).str.strip()

    dentro = int(codigos.isin(do_municipio).sum())
    fora = len(codigos) - dentro
    total = len(codigos)

    contagem = codigos.value_counts()
    principal_codigo = contagem.index[0]
    principal_total = int(contagem.iloc[0])

    detalhe = cnes_municipio[cnes_municipio["CNES"] == principal_codigo]
    leitos = 0
    if not detalhe.empty:
        # Com várias competências, os leitos vêm da mais recente.
        detalhe = detalhe[detalhe["competencia_ano"] == detalhe["competencia_ano"].max()]
        for coluna in ("QTLEITP1", "QTLEITP2", "QTLEITP3"):
            valor = pd.to_numeric(detalhe.iloc[0][coluna], errors="coerce")
            leitos += int(valor) if pd.notna(valor) else 0

    return {
        "total": total,
        "dentro": dentro,
        "fora": fora,
        "percentual_dentro": round(dentro / total * 100, 1),
        "ic_dentro": _wilson_percentual(dentro, total),
        "percentual_fora": round(fora / total * 100, 1),
        "ic_fora": _wilson_percentual(fora, total),
        "estabelecimentos_distintos": int(contagem.size),
        "principal_cnes": principal_codigo,
        "principal_internacoes": principal_total,
        "principal_percentual": round(principal_total / total * 100, 1),
        "ic_principal": _wilson_percentual(principal_total, total),
        "principal_leitos": leitos,
    }


def capacidade_hospitalar(
    cnes_municipio: pd.DataFrame,
    internacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Leitos, urgência e internações de cada hospital geral SUS do município."""
    colunas = ["cnes", "nome", "leitos", "urgencia", "internacoes"]
    if cnes_municipio.empty:
        return pd.DataFrame(columns=colunas)

    hospitais = cnes_municipio[
        (cnes_municipio["VINC_SUS"]) & (cnes_municipio["TP_UNID"] == "05")
    ].copy()

    if hospitais.empty:
        logger.warning("Nenhum hospital geral SUS no município")
        return pd.DataFrame(columns=colunas)

    leitos = 0
    for coluna in ("QTLEITP1", "QTLEITP2", "QTLEITP3"):
        leitos = leitos + pd.to_numeric(hospitais[coluna], errors="coerce").fillna(0)

    hospitais["leitos"] = leitos.astype(int)

    contagem = internacoes["CNES"].astype(str).str.strip().value_counts()
    hospitais["internacoes"] = hospitais["CNES"].map(contagem).fillna(0).astype(int)

    hospitais["nome"] = (
        hospitais["CNES"].map(config.CNES_NOMES).fillna("Estabelecimento " + hospitais["CNES"])
    )
    hospitais["urgencia"] = hospitais["URGEMERG"].map({True: "sim", False: "não"})

    return (
        hospitais[["CNES", "nome", "leitos", "urgencia", "internacoes"]]
        .rename(columns={"CNES": "cnes"})
        .sort_values("internacoes", ascending=False)
        .reset_index(drop=True)
    )
