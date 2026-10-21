"""Figuras de DDA (Sivep-DDA), Parauapebas × Pará × Brasil, nos anos de config.DDA_ANOS."""

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from dda import comum
from dda.limpeza_dda import corrigir_unidades
from src import config, graficos, relatorio

PRIMEIRO_ANO, ULTIMO_ANO = min(config.DDA_ANOS), max(config.DDA_ANOS)

# Linha cheia no primeiro ano e tracejada no último (dados preliminares)
ESTILOS_ANO = {
    PRIMEIRO_ANO: ("-", config.AZUL_OKABE_ITO),
    ULTIMO_ANO: ("--", config.VERMELHAO_OKABE_ITO),
}


def carregar(ano: int) -> pd.DataFrame:
    """Lê o parquet do ano, corrige unidades, recorta o período e soma os casos."""
    df = comum.ler_ano(ano)
    df = corrigir_unidades(df, mostrar=False)
    if ano == ULTIMO_ANO:
        df = df[df["sem_epid_week"] <= config.DDA_SE_MAX]
    df["casos"] = df[config.DDA_FAIXAS].sum(axis=1)
    return df


def casos_semanais(df: pd.DataFrame) -> pd.Series:
    """Casos de Parauapebas por semana epidemiológica."""
    residentes = df["municipio_ibge"] == config.MUNICIPIO_IBGE_6
    return df[residentes].groupby("sem_epid_week")["casos"].sum()


def por_unidade(df: pd.DataFrame) -> pd.Series:
    """Casos por unidade informante, por semana epidemiológica."""
    soma = df.groupby("sem_epid_week")[["casos", "nu_unidades_inf"]].sum()
    return soma["casos"] / soma["nu_unidades_inf"]


def recortes(df: pd.DataFrame) -> dict:
    return {
        config.MUNICIPIO_NOME: df[df["municipio_ibge"] == config.MUNICIPIO_IBGE_6],
        "Pará": df[df["uf_ibge"] == config.UF_IBGE],
        "Brasil": df,
    }


def rodape(local: str, extracao) -> str:
    """Rodapé das figuras: fonte, período até config.DDA_SE_MAX e data dos arquivos."""
    return relatorio.rodape_figura(
        f"Sivep-DDA (Ministério da Saúde), unidades sentinela, {local}",
        extracao,
        periodo=f"{PRIMEIRO_ANO} e {ULTIMO_ANO} até a semana epidemiológica {config.DDA_SE_MAX}",
    )


def main() -> None:
    comum.FIGURAS.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10})

    dados = {ano: carregar(ano) for ano in config.DDA_ANOS}
    extracao = comum.extracao_dda()
    municipio = f"{config.MUNICIPIO_NOME} ({config.MUNICIPIO_UF})"

    # Figura 1 – Casos semanais em Parauapebas, primeiro e último ano
    fig, ax = plt.subplots(figsize=(9, 4))

    for ano, df in dados.items():
        semanal = casos_semanais(df)
        linha, cor = ESTILOS_ANO[ano]
        ax.plot(
            semanal.index,
            semanal.values,
            linestyle=linha,
            color=cor,
            marker="o",
            markersize=3,
            label=str(ano),
        )

    # Destaque só nos pontos do último ano sujeitos a atraso
    semanal_ultimo = casos_semanais(dados[ULTIMO_ANO])
    atraso = semanal_ultimo[semanal_ultimo.index >= config.DDA_SE_ATRASO_INICIO]
    ax.scatter(
        atraso.index,
        atraso.values,
        s=60,
        facecolors="none",
        edgecolors="black",
        zorder=3,
        label=f"{ULTIMO_ANO}: semanas sujeitas a atraso",
    )

    ax.set_xlim(0.5, 53.5)
    ax.set_xticks(range(1, 54, 4))
    ax.set_ylim(0, None)
    ax.set_xlabel("Semana epidemiológica")
    ax.set_ylabel("Casos de DDA")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    graficos.desenhar_rodape(fig, rodape(municipio, extracao))
    fig.savefig(comum.FIGURAS / "figura1_dda_parauapebas_semanal.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Figura 2 – Casos por unidade informante: Parauapebas × Pará × Brasil
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4.3),
        sharey=True,
        gridspec_kw={"width_ratios": [53, config.DDA_SE_MAX]},
    )

    for ax, (ano, df) in zip(axes, dados.items(), strict=True):
        for nome, recorte in recortes(df).items():
            semanal = por_unidade(recorte)
            ax.plot(
                semanal.index,
                semanal.values,
                color=config.CORES_LOCAL[nome],
                marker="o",
                markersize=2.5,
                linewidth=1.3,
                label=nome,
            )
        ax.set_title(str(ano) + (" (dados preliminares)" if ano == ULTIMO_ANO else ""))
        ax.set_xlabel("Semana epidemiológica")
        ax.grid(alpha=0.3)
        ax.set_ylim(0, None)

    axes[0].set_xlim(0.5, 53.5)
    axes[0].set_xticks(range(1, 54, 4))
    axes[1].set_xlim(0.5, config.DDA_SE_MAX + 0.5)
    axes[1].set_xticks(range(1, config.DDA_SE_MAX + 1, 3))
    axes[1].axvspan(
        config.DDA_SE_ATRASO_INICIO - 0.5, config.DDA_SE_MAX + 0.5, color="grey", alpha=0.15
    )
    axes[0].set_ylabel("Casos por unidade informante")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda valor, _: relatorio.numero(valor)))

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.075), ncol=3, frameon=False
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    graficos.desenhar_rodape(fig, rodape(f"{municipio}, Pará e Brasil", extracao))
    fig.savefig(comum.FIGURAS / "figura2_dda_casos_por_unidade.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Figuras salvas em figuras/:")
    print(" - figura1_dda_parauapebas_semanal.png")
    print(" - figura2_dda_casos_por_unidade.png")


if __name__ == "__main__":
    main()
