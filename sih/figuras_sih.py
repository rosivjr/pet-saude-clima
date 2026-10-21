"""Figuras 3 (saneamento) e 4 (proporção de internações por diarreia)."""

import json
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sih import comum
from src import config, graficos, proveniencia, relatorio
from src.carregadores import carregar_sinisa

# Indicadores da Figura 3, na ordem das barras. O IES2003 tem como base a água
# consumida, em Parauapebas e no Brasil.
INDICADORES = {
    "IAG0001": "Atendimento com\nrede de água",
    "IES0001": "Atendimento com\nrede de esgoto",
    "IES2003": "Esgoto tratado\n(em relação à água consumida)",
    "IAG2013": "Perdas na distribuição (%)",
}
# Colunas de sih_agregado_brasil.csv (gravado por sih/sih_nacional.py) e o recorte de cada uma
RECORTES = {"parauapebas": config.MUNICIPIO_NOME, "para": "Pará", "brasil": "Brasil"}


def sinisa_parauapebas() -> tuple[list[float], object]:
    """Valores de Parauapebas no SINISA, na ordem de INDICADORES, e o ano de referência."""
    lidos = [carregar_sinisa(chave) for chave in ("agua", "esgoto")]
    valor = pd.concat([tabela for tabela, _ in lidos]).set_index("codigo")["valor"]
    return [float(valor[codigo]) for codigo in INDICADORES], lidos[0][1].get("ano_referencia")


def extracao_sih(caminho=comum.PROVENIENCIA) -> proveniencia.Extracao | None:
    """
    Datas de download dos arquivos em proveniencia_sih.json, para o rodapé da Figura 4.

    O formato anterior do JSON não tem data por arquivo; nesse caso, e sem o
    arquivo, devolve None e o rodapé diz que a data não foi registrada.
    """
    if not caminho.exists():
        return None
    arquivos = json.loads(caminho.read_text(encoding="utf-8")).get("arquivos", [])
    datas = [date.fromisoformat(a["baixado_em"][:10]) for a in arquivos if a.get("baixado_em")]
    return proveniencia.Extracao(min(datas), max(datas), True) if datas else None


def proporcao(tabela: pd.DataFrame, ano: int, meses: range) -> pd.Series:
    """Internações por diarreia (A00–A09) em % de todas, por recorte, no ano e meses dados."""
    periodo = tabela[(tabela["ano"] == ano) & (tabela["mes"].isin(meses))]
    total = periodo[list(RECORTES)].sum()
    diarreia = periodo.loc[periodo["grupo"] == "diarreia_A00_A09", list(RECORTES)].sum()
    return 100 * diarreia / total


def main() -> None:
    config.FIGURAS.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10})

    # Figura 3 – Saneamento: Parauapebas × Brasil (SINISA)
    indicadores = list(INDICADORES.values())
    parauapebas, ano_referencia = sinisa_parauapebas()
    valores = {
        config.MUNICIPIO_NOME: parauapebas,
        "Brasil": [config.SINISA_BRASIL[codigo] for codigo in INDICADORES],
    }

    fig, ax = plt.subplots(figsize=(8, 4.5))
    y = np.arange(len(indicadores))
    altura = 0.38
    for i, (nome, valores_local) in enumerate(valores.items()):
        posicao = y - altura / 2 + i * altura
        barras = ax.barh(
            posicao, valores_local, height=altura, color=config.CORES_LOCAL[nome], label=nome
        )
        for barra, valor in zip(barras, valores_local, strict=True):
            ax.text(
                valor + 1,
                barra.get_y() + barra.get_height() / 2,
                f"{relatorio.numero(valor)}%",
                va="center",
                fontsize=9,
            )

    ax.set_yticks(y)
    ax.set_yticklabels(indicadores)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("Percentual (%)")
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    graficos.desenhar_rodape(
        fig,
        relatorio.rodape_figura(
            f"SINISA (Ministério das Cidades), {config.MUNICIPIO_NOME} "
            f"({config.MUNICIPIO_UF}) e Brasil",
            proveniencia.datas_de_extracao("SINISA"),
            periodo=f"ano de referência {ano_referencia}",
        ),
    )
    fig.savefig(
        config.FIGURAS / "figura3_saneamento_parauapebas_brasil.png", dpi=300, bbox_inches="tight"
    )
    plt.close(fig)

    # Figura 4 – Proporção de internações por diarreia (A00–A09)
    tabela = pd.read_csv(config.DADOS_PROCESSADOS / "sih_agregado_brasil.csv")
    meses = config.SIH_MESES_COMPARACAO
    rotulo_meses = comum.rotulo_meses(meses, abreviado=True)
    primeiro_ano, ultimo_ano = min(config.DDA_ANOS), max(config.DDA_ANOS)
    periodos = [
        (f"{primeiro_ano}\n(ano completo)", proporcao(tabela, primeiro_ano, range(1, 13))),
        (f"{rotulo_meses}\n{primeiro_ano}", proporcao(tabela, primeiro_ano, meses)),
        (f"{rotulo_meses}\n{ultimo_ano}", proporcao(tabela, ultimo_ano, meses)),
    ]
    print("Proporções usadas na Figura 4 (%):")
    for rotulo, percentuais in periodos:
        print(rotulo.replace("\n", " "), percentuais.round(2).to_dict())

    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(periodos))
    largura = 0.26
    for i, (coluna, nome) in enumerate(RECORTES.items()):
        valores_local = [percentuais[coluna] for _, percentuais in periodos]
        barras = ax.bar(
            x - largura + i * largura,
            valores_local,
            width=largura,
            color=config.CORES_LOCAL[nome],
            label=nome,
        )
        for barra, valor in zip(barras, valores_local, strict=True):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                valor + 0.05,
                relatorio.numero(valor, 2),
                ha="center",
                fontsize=8,
            )

    ax.set_xticks(x)
    ax.set_xticklabels([rotulo for rotulo, _ in periodos])
    ax.set_ylabel("% das internações pelo SUS")
    ax.set_ylim(0, 3.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda valor, _: relatorio.numero(valor)))
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper center", ncol=3, frameon=False)
    fig.tight_layout()
    graficos.desenhar_rodape(
        fig,
        relatorio.rodape_figura(
            f"SIH/SUS, internações de residentes por data de internação, "
            f"{config.MUNICIPIO_NOME} ({config.MUNICIPIO_UF}), Pará e Brasil",
            extracao_sih(),
            periodo=f"{primeiro_ano} e {rotulo_meses.lower()} de {ultimo_ano}",
        ),
    )
    fig.savefig(
        config.FIGURAS / "figura4_proporcao_internacoes_diarreia.png", dpi=300, bbox_inches="tight"
    )
    plt.close(fig)

    print("\nFiguras salvas em figuras/:")
    print(" - figura3_saneamento_parauapebas_brasil.png")
    print(" - figura4_proporcao_internacoes_diarreia.png")


if __name__ == "__main__":
    main()
