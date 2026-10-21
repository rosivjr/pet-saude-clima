"""
Figuras do relatório: conformidade e E. coli na água, sazonalidade, internações
por grupo, capacidade hospitalar, perfil etário, série do cloro e origem da
captação, com o rodapé de fonte e data de extração.

Não calcula nada e não acessa fonte de dado: recebe resultados já calculados.
A paleta (no config) e o rodapé também servem às figuras de dda/ e
sih/figuras_sih.py.
"""

import logging
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")  # backend sem janela, para gerar arquivo em qualquer ambiente
import matplotlib.pyplot as plt

from src import config
from src.relatorio import milhar, numero

logger = logging.getLogger(__name__)

PASTA_FIGURAS = config.FIGURAS


def _preparar_eixos(titulo: str, tamanho=(9, 5)):
    """
    Cria figura e eixos com o estilo padrão do relatório e o título dado.

    O tamanho é largura e altura em polegadas.
    """
    fig, ax = plt.subplots(figsize=tamanho)
    ax.set_title(titulo, fontsize=13, color=config.TEAL_ESCURO, pad=15, loc="left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(config.COR_EIXOS)
    ax.spines["bottom"].set_color(config.COR_EIXOS)
    ax.tick_params(colors=config.CINZA, labelsize=10)
    return fig, ax


def desenhar_rodape(fig, texto: str | None) -> None:
    """
    Escreve sob a figura o rodapé de relatorio.rodape_figura (fonte, período, extração).

    Usada também pelas figuras de dda/ e de sih/figuras_sih.py.
    """
    if texto:
        fig.text(0.01, -0.02, texto, fontsize=8, color=config.CINZA, ha="left", va="top", wrap=True)


def _salvar(fig, nome: str, rodape: str | None = None) -> Path:
    """
    Desenha o rodapé, salva a figura na pasta de saída e fecha para liberar memória.

    O nome do arquivo vem sem extensão; o rodapé é o texto de
    relatorio.rodape_figura.
    """
    desenhar_rodape(fig, rodape)
    PASTA_FIGURAS.mkdir(exist_ok=True)
    caminho = PASTA_FIGURAS / f"{nome}.png"
    fig.tight_layout()
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Figura salva: %s", caminho.name)
    return caminho


def _erro_ic(valores, inferiores, superiores) -> list[list[float]]:
    """Distâncias do valor até os limites do IC, no formato xerr/yerr do matplotlib."""
    return [
        [v - i for v, i in zip(valores, inferiores, strict=True)],
        [s - v for v, s in zip(valores, superiores, strict=True)],
    ]


def _barras_ic(ax, barras, inferiores, superiores, valores) -> None:
    """Desenha o IC95% de Wilson sobre barras horizontais."""
    ax.errorbar(
        valores,
        [b.get_y() + b.get_height() / 2 for b in barras],
        xerr=_erro_ic(valores, inferiores, superiores),
        fmt="none",
        ecolor=config.CINZA,
        elinewidth=1.2,
        capsize=3,
    )


def grafico_conformidade_agua(
    resultados, microbiologico: pd.DataFrame, rodape: str | None = None
) -> Path:
    """
    Gera o gráfico de amostras fora do padrão (físico-químicos) ou com
    presença (microbiológicos), por parâmetro de qualidade da água.

    Todas as barras têm a mesma cor: nenhuma norma define um corte entre
    "muito" e "pouco". O valor e o número de amostras vão
    escritos ao lado de cada barra, para que nada dependa só da cor. Recebe
    os resultados de indicadores.avaliar_conformidade_agua() e
    indicadores.avaliar_microbiologico(); o rodapé é o texto de
    relatorio.rodape_figura.
    """
    rotulos, valores, inferiores, superiores, amostras = [], [], [], [], []

    for r in resultados:
        nome = r.parametro.split(" (")[0]
        rotulos.append(nome)
        valores.append(r.percentual_fora)
        inferiores.append(r.ic_inferior)
        superiores.append(r.ic_superior)
        amostras.append(r.total_amostras)

    for _, linha in microbiologico.iterrows():
        rotulos.append(str(linha["PARAMETRO"]))
        valores.append(float(linha["percentual_presenca"]))
        inferiores.append(float(linha["ic_inferior"]))
        superiores.append(float(linha["ic_superior"]))
        amostras.append(int(linha["total"]))

    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    rotulos = [rotulos[i] for i in ordem]
    valores = [valores[i] for i in ordem]
    inferiores = [inferiores[i] for i in ordem]
    superiores = [superiores[i] for i in ordem]
    amostras = [amostras[i] for i in ordem]

    fig, ax = _preparar_eixos(
        "Amostras fora do padrão (físico-químicos) ou com presença (microbiológicos), %",
        (9, 4.5),
    )
    barras = ax.barh(rotulos, valores, color=config.AZUL_OKABE_ITO)
    _barras_ic(ax, barras, inferiores, superiores, valores)
    ax.set_xlim(0, 125)
    ax.set_xlabel("% das amostras (barra: IC95% de Wilson)", fontsize=10, color=config.CINZA)
    ax.grid(axis="x", color="#EEF4F5", zorder=0)
    ax.set_axisbelow(True)

    for barra, valor, sup, n in zip(barras, valores, superiores, amostras, strict=True):
        ax.text(
            sup + 1.5,
            barra.get_y() + barra.get_height() / 2,
            f"{numero(valor)}%  (n = {milhar(n)})",
            va="center",
            fontsize=10,
            color=config.TEAL_ESCURO,
            fontweight="bold",
        )

    return _salvar(fig, "01_conformidade_agua", rodape)


def grafico_ecoli_por_area(
    ecoli_por_area: pd.DataFrame,
    rodape: str | None = None,
) -> Path | None:
    """
    Gera o gráfico de positividade para E. coli por área de abrangência.

    Exibe apenas áreas com base amostral suficiente, para evitar leitura
    indevida de percentuais calculados sobre poucas amostras, até
    config.FIGURA_ECOLI_MAX_AREAS áreas. Sem nenhuma área suficiente, não
    gera a figura, registra o motivo e devolve None.

    Args:
        ecoli_por_area: DataFrame de indicadores.ecoli_por_area().
        rodape: texto de relatorio.rodape_figura.
    """
    robustas = ecoli_por_area[ecoli_por_area["amostras"] >= config.LIMIAR_AMOSTRAS_PROPORCAO].head(
        config.FIGURA_ECOLI_MAX_AREAS
    )
    if robustas.empty:
        logger.warning(
            "Figura 02 não gerada: nenhuma área com %d amostras de E. coli ou mais",
            config.LIMIAR_AMOSTRAS_PROPORCAO,
        )
        return None

    dados = robustas.sort_values("percentual_positivo")

    fig, ax = _preparar_eixos("Amostras com E. coli presente por área (%)", (9, 5.5))

    barras = ax.barh(
        dados["area"].str.title(), dados["percentual_positivo"], color=config.AZUL_OKABE_ITO
    )
    _barras_ic(
        ax, barras, dados["ic_inferior"], dados["ic_superior"], list(dados["percentual_positivo"])
    )
    ax.set_xlim(0, float(dados["ic_superior"].max()) * 1.35)
    ax.set_xlabel(
        "% das amostras com E. coli (barra: IC95% de Wilson)", fontsize=10, color=config.CINZA
    )
    ax.grid(axis="x", color="#EEF4F5")
    ax.set_axisbelow(True)

    for barra, valor, n, sup in zip(
        barras, dados["percentual_positivo"], dados["amostras"], dados["ic_superior"], strict=True
    ):
        ax.text(
            sup + 1,
            barra.get_y() + barra.get_height() / 2,
            f"{numero(valor)}%  (n={n})",
            va="center",
            fontsize=9,
            color=config.TEAL_ESCURO,
        )

    return _salvar(fig, "02_ecoli_por_area", rodape)


def grafico_sazonalidade(sazonal: pd.DataFrame, rodape: str | None = None) -> Path:
    """
    Gera a série mensal do percentual de amostras com E. coli presente.

    Args:
        sazonal: DataFrame de indicadores.sazonalidade_ecoli().
        rodape: texto de relatorio.rodape_figura.
    """
    dados = sazonal.sort_values(["ano", "mes"])
    rotulos = [
        f"{config.MESES_ABREV[int(m)]}/{str(int(a))[2:]}"
        for a, m in zip(dados["ano"], dados["mes"], strict=True)
    ]

    fig, ax = _preparar_eixos("Amostras com E. coli presente ao longo do tempo (%)", (10, 4.5))
    ax.plot(
        rotulos,
        dados["percentual_positivo"],
        marker="o",
        color=config.TEAL,
        linewidth=2.2,
        markersize=6,
    )
    ax.fill_between(
        rotulos,
        dados["ic_inferior"],
        dados["ic_superior"],
        alpha=0.15,
        color=config.TEAL,
        label="IC95% de Wilson",
    )
    ax.legend(frameon=False, fontsize=9)
    ax.set_ylabel("% das amostras", fontsize=10, color=config.CINZA)
    ax.grid(axis="y", color="#EEF4F5")
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    return _salvar(fig, "03_sazonalidade_ecoli", rodape)


def grafico_internacoes_por_grupo(perfis, rodape: str | None = None) -> Path:
    """Gera o gráfico de internações por grupo de agravo DRSAI."""
    drsai = [p for p in perfis if p.grupo in config.GRUPOS_DRSAI]
    drsai = sorted(drsai, key=lambda p: p.internacoes)

    fig, ax = _preparar_eixos("Internações por grupo de agravo relacionado ao saneamento", (9, 4.5))
    barras = ax.barh([p.grupo for p in drsai], [p.internacoes for p in drsai], color=config.TEAL)
    ax.set_xlabel("Internações", fontsize=10, color=config.CINZA)
    ax.grid(axis="x", color="#EEF4F5")
    ax.set_axisbelow(True)

    maximo = max(p.internacoes for p in drsai) if drsai else 1
    ax.set_xlim(0, maximo * 1.15)

    for barra, p in zip(barras, drsai, strict=True):
        ax.text(
            barra.get_width() + maximo * 0.015,
            barra.get_y() + barra.get_height() / 2,
            str(p.internacoes),
            va="center",
            fontsize=10,
            color=config.TEAL_ESCURO,
            fontweight="bold",
        )

    return _salvar(fig, "04_internacoes_por_grupo", rodape)


def grafico_capacidade_hospitalar(hospitais: pd.DataFrame, rodape: str | None = None) -> Path:
    """
    Compara leitos cadastrados e internações por hospital.

    Evidencia se a concentração das internações reflete ausência de
    capacidade ou concentração de demanda.

    Args:
        hospitais: DataFrame de indicadores.capacidade_hospitalar().
        rodape: texto de relatorio.rodape_figura.
    """
    dados = hospitais.sort_values("leitos")
    nomes = [n if len(n) <= 28 else n[:26] + "..." for n in dados["nome"]]

    posicoes = range(len(dados))
    altura = 0.38

    fig, ax = _preparar_eixos("Leitos cadastrados e internações por hospital", (9.5, 5))
    ax.barh(
        [p + altura / 2 for p in posicoes],
        dados["leitos"],
        height=altura,
        color=config.TEAL,
        label="Leitos cadastrados",
    )
    ax.barh(
        [p - altura / 2 for p in posicoes],
        dados["internacoes"],
        height=altura,
        color=config.VERMELHO,
        label="Internações no período",
    )
    ax.set_yticks(list(posicoes))
    ax.set_yticklabels(nomes, fontsize=9)
    # Um hospital concentra quase todas as internações; em escala linear os
    # demais nem apareceriam. symlog, e não log, porque há hospitais com zero.
    ax.set_xscale("symlog")
    ax.set_xlabel(
        "Escala logarítmica simétrica (linear perto de zero)", fontsize=9, color=config.CINZA
    )
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.grid(axis="x", color="#EEF4F5")
    ax.set_axisbelow(True)

    return _salvar(fig, "05_capacidade_hospitalar", rodape)


def grafico_perfil_etario_comparado(
    etario_geral: pd.DataFrame,
    etario_feco: pd.DataFrame,
    rodape: str | None = None,
) -> Path:
    """
    Compara a distribuição etária do conjunto DRSAI com a do grupo feco-oral.

    O contraste evidencia que as doenças de transmissão feco-oral atingem
    crianças pequenas de forma desproporcional, o que a média dos grupos
    esconde.

    Args:
        etario_geral: distribuição de indicadores.perfil_etario().
        etario_feco: distribuição de indicadores.perfil_etario_feco_oral().
        rodape: texto de relatorio.rodape_figura.
    """
    faixas = list(config.FAIXA_ETARIA_ROTULOS)

    def _percentuais(df: pd.DataFrame) -> list[float]:
        mapa = dict(zip(df["faixa_etaria"].astype(str), df["percentual"], strict=True))
        return [float(mapa.get(f, 0)) for f in faixas]

    geral = _percentuais(etario_geral)
    feco = _percentuais(etario_feco)

    posicoes = range(len(faixas))
    largura = 0.38

    fig, ax = _preparar_eixos(
        "Distribuição etária: conjunto DRSAI e agravos feco-orais (%)", (9, 4.5)
    )
    ax.bar(
        [p - largura / 2 for p in posicoes],
        geral,
        width=largura,
        color=config.CINZA,
        label="Todos os agravos DRSAI",
    )
    ax.bar(
        [p + largura / 2 for p in posicoes],
        feco,
        width=largura,
        color=config.TEAL,
        label="Agravos feco-orais",
    )
    ax.set_xticks(list(posicoes))
    ax.set_xticklabels(faixas)
    ax.set_xlabel("Faixa etária (anos)", fontsize=10, color=config.CINZA)
    ax.set_ylabel("% das internações", fontsize=10, color=config.CINZA)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color="#EEF4F5")
    ax.set_axisbelow(True)

    for pos, valor in zip(posicoes, feco, strict=True):
        if valor >= 20:
            ax.text(
                pos + largura / 2,
                valor + 1,
                f"{numero(valor)}%",
                ha="center",
                fontsize=9,
                color=config.TEAL_ESCURO,
                fontweight="bold",
            )

    return _salvar(fig, "06_perfil_etario_comparado", rodape)


def grafico_serie_cloro(serie: pd.DataFrame, rodape: str | None = None) -> Path:
    """
    Gera a série mensal do cloro residual, com o limite legal em destaque.

    Args:
        serie: DataFrame de indicadores.serie_mensal() para o cloro.
        rodape: texto de relatorio.rodape_figura.
    """
    dados = serie.sort_values(["ano", "mes"])
    rotulos = [
        f"{config.MESES_ABREV[int(m)]}/{str(int(a))[2:]}"
        for a, m in zip(dados["ano"], dados["mes"], strict=True)
    ]

    fig, ax = _preparar_eixos("Cloro residual livre medido e limite legal (mg/L)", (10, 4.5))
    ax.plot(
        rotulos,
        dados["media"],
        marker="o",
        color=config.TEAL,
        linewidth=2.2,
        markersize=6,
        label="Média medida",
    )
    ax.axhline(
        config.CLORO_RESIDUAL_MINIMO,
        color=config.VERMELHO,
        linestyle="--",
        linewidth=1.6,
        label=f"Mínimo legal ({config.CLORO_RESIDUAL_MINIMO} mg/L)",
    )
    ax.set_ylabel("mg/L", fontsize=10, color=config.CINZA)
    ax.set_ylim(0, max(0.35, float(dados["media"].max()) * 1.3))
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color="#EEF4F5")
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    return _salvar(fig, "07_serie_cloro", rodape)


def grafico_origem_captacao(por_captacao: pd.DataFrame, rodape: str | None = None) -> Path:
    """
    Gera o gráfico de amostras com E. coli presente por origem da captação da água.

    Args:
        por_captacao: DataFrame de indicadores.ecoli_por_captacao().
        rodape: texto de relatorio.rodape_figura.
    """
    dados = por_captacao.sort_values("percentual_positivo")

    fig, ax = _preparar_eixos(
        "Amostras com E. coli presente segundo a origem da água (%)",
        (9, 3.8),
    )

    barras = ax.barh(dados["origem"], dados["percentual_positivo"], color=config.AZUL_OKABE_ITO)
    _barras_ic(
        ax, barras, dados["ic_inferior"], dados["ic_superior"], list(dados["percentual_positivo"])
    )
    ax.set_xlim(0, float(dados["ic_superior"].max()) * 1.4)
    ax.set_xlabel(
        "% das amostras com E. coli (barra: IC95% de Wilson)", fontsize=10, color=config.CINZA
    )
    ax.grid(axis="x", color="#EEF4F5")
    ax.set_axisbelow(True)

    for barra, valor, n, sup in zip(
        barras, dados["percentual_positivo"], dados["amostras"], dados["ic_superior"], strict=True
    ):
        ax.text(
            sup + 0.8,
            barra.get_y() + barra.get_height() / 2,
            f"{numero(valor)}%  (n={n})",
            va="center",
            fontsize=9,
            color=config.TEAL_ESCURO,
        )

    return _salvar(fig, "08_origem_captacao", rodape)


def gerar_todos(
    conformidade,
    microbiologico: pd.DataFrame,
    ecoli_area: pd.DataFrame,
    sazonal: pd.DataFrame,
    perfis,
    hospitais: pd.DataFrame,
    etario_geral: pd.DataFrame,
    etario_feco: pd.DataFrame,
    serie_cloro: pd.DataFrame,
    captacao: pd.DataFrame,
    rodapes: dict[str, str] | None = None,
) -> list[Path]:
    """
    Gera todas as figuras do relatório.

    Falhas individuais são registradas e não interrompem a geração das
    demais, pois a visualização é complementar ao relatório em texto. Os
    rodapés são textos de relatorio.rodape_figura nas chaves "agua"
    (SISAGUA), "internacoes" (SIH) e "hospitais" (CNES e SIH). Devolve os
    caminhos das figuras geradas.
    """
    rodapes = rodapes or {}
    agua, internacoes = rodapes.get("agua"), rodapes.get("internacoes")
    tarefas = [
        (
            "conformidade da água",
            lambda: grafico_conformidade_agua(conformidade, microbiologico, agua),
        ),
        ("E. coli por área", lambda: grafico_ecoli_por_area(ecoli_area, rodape=agua)),
        ("sazonalidade", lambda: grafico_sazonalidade(sazonal, agua)),
        ("internações por grupo", lambda: grafico_internacoes_por_grupo(perfis, internacoes)),
        (
            "capacidade hospitalar",
            lambda: grafico_capacidade_hospitalar(hospitais, rodapes.get("hospitais")),
        ),
        (
            "perfil etário comparado",
            lambda: grafico_perfil_etario_comparado(etario_geral, etario_feco, internacoes),
        ),
        ("série do cloro", lambda: grafico_serie_cloro(serie_cloro, agua)),
        ("origem da captação", lambda: grafico_origem_captacao(captacao, agua)),
    ]

    gerados = []
    for nome, funcao in tarefas:
        try:
            caminho = funcao()
        # Eixo sem valores ou falha ao gravar o PNG. Coluna ausente (KeyError)
        # é erro de código ou de carregador e interrompe a execução.
        except (ValueError, OSError) as erro:
            logger.warning("Falha ao gerar o gráfico de %s: %s", nome, type(erro).__name__)
            continue
        # None: a própria função não gerou a figura e já registrou o motivo.
        if caminho is not None:
            gerados.append(caminho)

    logger.info("%d de %d figuras geradas", len(gerados), len(tarefas))
    return gerados
