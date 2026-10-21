"""Cobertura de saneamento no Censo 2022 e cumprimento do plano de amostragem do Vigiagua."""

import math

import pandas as pd

from src import config


def cobertura_censo(
    tabela: pd.DataFrame,
    subcategorias: set[str] | None = None,
) -> pd.DataFrame:
    """
    Proporção de domicílios em cada categoria de uma tabela do Censo 2022.

    O Censo é uma contagem de todos os domicílios, não uma amostra, então
    não há intervalo de confiança. Subcategorias (nível 2) são as que têm
    ' - ' no nome ou estão em `subcategorias`; somá-las à categoria de cima
    contaria o mesmo domicílio duas vezes.

    Args:
        tabela: resultado de carregadores.carregar_censo_sidra().
        subcategorias: nomes que são subdivisão da linha anterior
                       (config.CENSO_2022_SUBCATEGORIAS).

    Returns:
        DataFrame com categoria, nível (0 total, 1 categoria, 2
        subcategoria), domicílios e percentual do total.
    """
    subcategorias = subcategorias or set()
    if tabela.empty:
        return pd.DataFrame(columns=["categoria", "nivel", "domicilios", "percentual"])

    total = float(tabela["domicilios"].iloc[0])
    resultado = tabela.copy()
    resultado["nivel"] = [
        0 if i == 0 else (2 if (" - " in c or c in subcategorias) else 1)
        for i, c in enumerate(resultado["categoria"])
    ]
    resultado["percentual"] = (resultado["domicilios"] / total * 100).round(2)
    return resultado[["categoria", "nivel", "domicilios", "percentual"]]


def conferir_subcategorias(cobertura: pd.DataFrame) -> list[str]:
    """Categorias cujas subcategorias não somam o total delas (vazia se tudo confere)."""
    divergentes = []
    pai, soma = None, 0.0
    for _, reg in cobertura.iterrows():
        if reg["nivel"] == 2:
            soma += reg["domicilios"]
            continue
        if pai is not None and soma and abs(soma - pai["domicilios"]) > 0.5:
            divergentes.append(pai["categoria"])
        pai, soma = (reg, 0.0) if reg["nivel"] == 1 else (None, 0.0)
    if pai is not None and soma and abs(soma - pai["domicilios"]) > 0.5:
        divergentes.append(pai["categoria"])
    return divergentes


def _minimo_com_arredondamento(populacao: int, regra: str) -> int:
    """Mínimo mensal com uma regra de arredondamento explícita."""
    for limite, fixas, por_extra in config.PLANO_AMOSTRAGEM_FAIXAS:
        if limite is None or populacao <= limite:
            if por_extra is None:
                return fixas
            arredondar = math.ceil if regra == "cima" else math.floor
            return fixas + arredondar(populacao / por_extra)
    raise ValueError(f"População fora das faixas: {populacao}")


def minimo_mensal_amostras(populacao: int) -> int:
    """
    Número mínimo mensal de amostras pela Diretriz Nacional do Vigiagua.

    Usado para cloro residual livre, turbidez e coliformes totais/E. coli.
    O arredondamento da parcela variável segue
    config.PLANO_AMOSTRAGEM_ARREDONDAMENTO.
    """
    return _minimo_com_arredondamento(populacao, config.PLANO_AMOSTRAGEM_ARREDONDAMENTO)


def cumprimento_plano_amostragem(agua: pd.DataFrame) -> pd.DataFrame:
    """
    Amostras de vigilância realizadas por ano, comparadas com o mínimo mensal.

    Para cada ano e parâmetro do plano básico: meses do período, meses com
    alguma coleta, meses que atingiram o mínimo, total de amostras, total
    mínimo exigido (mínimo mensal x meses) e percentual cumprido. A coluna
    meses_sem_coleta lista os meses (1 a 12) sem nenhuma amostra.
    """
    colunas = [
        "ano",
        "parametro",
        "populacao",
        "minimo_mensal",
        "meses_periodo",
        "meses_com_coleta",
        "meses_minimo_atingido",
        "minimo_mensal_baixo",
        "meses_minimo_baixo",
        "amostras",
        "minimo_total",
        "percentual_cumprido",
        "meses_sem_coleta",
    ]
    linhas = []

    for ano in range(config.PERIODO_INICIO.year, config.PERIODO_FIM.year + 1):
        mes_inicial = config.PERIODO_INICIO.month if ano == config.PERIODO_INICIO.year else 1
        mes_final = config.PERIODO_FIM.month if ano == config.PERIODO_FIM.year else 12
        meses = list(range(mes_inicial, mes_final + 1))

        populacao = config.POPULACAO_ANUAL[ano]
        minimo = minimo_mensal_amostras(populacao)

        for parametro in config.PLANO_AMOSTRAGEM_PARAMETROS:
            do_ano = agua[(agua["ano"] == ano) & (agua["PARAMETRO"] == parametro)]
            por_mes = do_ano["mes"].value_counts()
            contagens = [int(por_mes.get(m, 0)) for m in meses]
            minimo_total = minimo * len(meses)
            minimo_baixo = _minimo_com_arredondamento(populacao, "baixo")

            linhas.append(
                {
                    "ano": ano,
                    "parametro": parametro,
                    "populacao": populacao,
                    "minimo_mensal": minimo,
                    "meses_periodo": len(meses),
                    "meses_com_coleta": sum(c > 0 for c in contagens),
                    "meses_minimo_atingido": sum(c >= minimo for c in contagens),
                    "minimo_mensal_baixo": minimo_baixo,
                    "meses_minimo_baixo": sum(c >= minimo_baixo for c in contagens),
                    "amostras": sum(contagens),
                    "minimo_total": minimo_total,
                    "percentual_cumprido": round(sum(contagens) / minimo_total * 100, 1),
                    "meses_sem_coleta": [
                        m for m, c in zip(meses, contagens, strict=True) if c == 0
                    ],
                }
            )

    return pd.DataFrame(linhas, columns=colunas)
