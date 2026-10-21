"""Seções de cloro e E. coli por área, ponto de coleta, captação e mês."""

import pandas as pd

from src import config

from ._formato import numero, subtitulo, titulo


def _tabela_proporcao(
    df: pd.DataFrame,
    coluna_rotulo: str,
    coluna_sucessos: str,
    coluna_percentual: str,
    rotulo: str,
    rotulo_sucessos: str,
    largura: int = 34,
    marcar_pequenas: bool = False,
) -> list[str]:
    """Tabela de proporções com n, casos, percentual e IC de Wilson."""
    saida = [
        f"  {rotulo:<{largura}}{'Amostras':>9}{rotulo_sucessos:>11}{'%':>8}  IC95%",
        f"  {'-' * (largura + 42)}",
    ]
    for _, reg in df.iterrows():
        marca = ""
        if marcar_pequenas and reg["amostras"] < config.LIMIAR_AMOSTRAS_PROPORCAO:
            marca = "  [!]"
        saida.append(
            f"  {str(reg[coluna_rotulo])[: largura - 1]:<{largura}}"
            f"{int(reg['amostras']):>9}"
            f"{int(reg[coluna_sucessos]):>11}"
            f"{numero(reg[coluna_percentual]) + '%':>8}  "
            f"{numero(reg['ic_inferior'])}–{numero(reg['ic_superior'])}%{marca}"
        )
    return saida


def secao_territorial(
    cloro_por_area: pd.DataFrame,
    ecoli_por_area: pd.DataFrame,
    resumo_cloro: dict,
    limite_linhas: int = 12,
) -> str:
    """
    Formata a distribuição territorial da qualidade da água.

    Usa a área de abrangência registrada no SISAGUA (Meta 1 do Eixo II).
    Só descreve; a comparação entre áreas não controla o número de coletas
    por solução. Cada bloco mostra no máximo limite_linhas áreas.
    """
    linhas = [titulo("11. DISTRIBUIÇÃO TERRITORIAL DA QUALIDADE DA ÁGUA")]
    linhas.append(
        "Agrupamento por área de abrangência registrada no SISAGUA.\n"
        f"Áreas com menos de {config.LIMIAR_AMOSTRAS_PROPORCAO} amostras aparecem "
        "marcadas com [!].\n"
    )

    linhas.append(subtitulo("Cloro residual abaixo do mínimo legal"))
    if cloro_por_area.empty:
        linhas.append("  Sem dados por área.\n")
    else:
        linhas.extend(
            _tabela_proporcao(
                cloro_por_area.head(limite_linhas),
                "area",
                "fora_do_padrao",
                "percentual_fora",
                "Área",
                "Fora",
                largura=26,
                marcar_pequenas=True,
            )
        )
        linhas.append(
            f"\n  Áreas com amostra de cloro ............ {resumo_cloro['areas']}\n"
            f"  Com base suficiente ................... {resumo_cloro['suficientes']}\n"
            f"  Destas, com 100% abaixo do mínimo ..... {resumo_cloro['todas_fora']}"
        )

    linhas.append(subtitulo("Presença de Escherichia coli — maior positividade"))
    if ecoli_por_area.empty:
        linhas.append("  Sem dados por área.\n")
        return "\n".join(linhas)

    linhas.extend(
        _tabela_proporcao(
            ecoli_por_area.head(limite_linhas),
            "area",
            "positivos",
            "percentual_positivo",
            "Área",
            "Positivos",
            largura=26,
            marcar_pequenas=True,
        )
    )

    robustas = ecoli_por_area[ecoli_por_area["amostras"] >= config.LIMIAR_AMOSTRAS_PROPORCAO]
    menores = robustas.tail(6).sort_values("percentual_positivo")

    if not menores.empty:
        linhas.append(subtitulo("Presença de Escherichia coli — menor positividade"))
        linhas.append(f"  Só áreas com {config.LIMIAR_AMOSTRAS_PROPORCAO} amostras ou mais.\n")
        linhas.extend(
            _tabela_proporcao(
                menores,
                "area",
                "positivos",
                "percentual_positivo",
                "Área",
                "Positivos",
                largura=26,
            )
        )

    return "\n".join(linhas) + "\n"


def secao_ecoli(
    por_captacao: pd.DataFrame,
    por_ponto: pd.DataFrame,
    sazonal: pd.DataFrame,
) -> str:
    """
    Formata o percentual de amostras com E. coli presente por categoria:
    origem da água, ponto de coleta e mês.

    Descritivo. Amostras da mesma solução não são independentes, então os
    intervalos subestimam a incerteza e diferenças pequenas entre
    categorias não devem ser lidas como associação.
    """
    linhas = [titulo("14. ESCHERICHIA COLI SEGUNDO ORIGEM, PONTO E MÊS")]
    linhas.append(
        "Descritivo. Coletas repetidas na mesma solução não são\n"
        "independentes; os intervalos subestimam a incerteza.\n"
    )

    linhas.append(subtitulo("Origem da água (cadastro da solução)"))
    if por_captacao.empty:
        linhas.append("  Cruzamento não disponível.\n")
    else:
        ligacao = por_captacao.attrs.get("ligacao")
        if ligacao:
            linhas.append(
                "  Ligação de cada amostra ao cadastro da solução:\n"
                f"    mesmo ano ............. {ligacao['mesmo_ano']}\n"
                f"    ano anterior .......... {ligacao['ano_anterior']}\n"
                f"    ano seguinte .......... {ligacao['ano_seguinte']}\n"
                f"    sem cadastro .......... {ligacao['sem_par']}\n"
            )
        linhas.extend(
            _tabela_proporcao(
                por_captacao,
                "origem",
                "positivos",
                "percentual_positivo",
                "Origem",
                "Positivos",
            )
        )
        linhas.append("\n  O cadastro não distingue poço raso de poço profundo.")

    linhas.append(subtitulo("Ponto de coleta"))
    if por_ponto.empty:
        linhas.append("  Cruzamento não disponível.\n")
    else:
        linhas.extend(
            _tabela_proporcao(
                por_ponto,
                "ponto",
                "positivos",
                "percentual_positivo",
                "Ponto",
                "Positivos",
                marcar_pequenas=True,
            )
        )

    linhas.append(subtitulo("Série mensal"))
    if sazonal.empty:
        linhas.append("  Série não disponível.\n")
        return "\n".join(linhas) + "\n"

    sazonal = sazonal.assign(
        rotulo=[
            f"{int(a)} {config.MESES_ABREV[int(m)]}"
            for a, m in zip(sazonal["ano"], sazonal["mes"], strict=True)
        ]
    )
    linhas.extend(
        _tabela_proporcao(
            sazonal,
            "rotulo",
            "positivos",
            "percentual_positivo",
            "Mês",
            "Positivos",
            largura=12,
            marcar_pequenas=True,
        )
    )
    linhas.append(
        "\n  Meses ausentes não tiveram coleta registrada. A comparação com\n"
        "  a chuva de cada mês está na seção 21."
    )

    return "\n".join(linhas) + "\n"
