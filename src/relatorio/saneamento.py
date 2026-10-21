"""Seções de saneamento: Censo 2022, SINISA e plano de amostragem do Vigiagua."""

import textwrap

import pandas as pd

from src import config

from ._formato import milhar, numero, subtitulo, titulo


def secao_censo(coberturas: dict[str, pd.DataFrame] | None) -> str:
    """
    Formata a cobertura de saneamento dos domicílios no Censo 2022.

    coberturas mapeia 'agua', 'esgoto' e 'lixo' ao resultado de
    indicadores.cobertura_censo; None quando os arquivos não estão disponíveis.
    """
    linhas = [titulo("18. SANEAMENTO DOS DOMICÍLIOS — CENSO 2022")]
    if not coberturas:
        linhas.append("  Tabelas do Censo 2022 não disponíveis nesta execução.\n")
        return "\n".join(linhas)

    linhas.append(
        "Fonte: IBGE, Censo Demográfico 2022, SIDRA. Domicílios particulares\n"
        "permanentes ocupados. Contagem de todos os domicílios, sem IC.\n"
    )
    for chave, (_, descricao) in config.CENSO_2022_TABELAS.items():
        tabela = coberturas.get(chave)
        linhas.append(subtitulo(descricao))
        if tabela is None or tabela.empty:
            linhas.append("  Não disponível.")
            continue
        for _, reg in tabela.iterrows():
            nome = reg["categoria"].split(" - ")[-1] if reg["nivel"] == 2 else reg["categoria"]
            recuo = "  " + "    " * max(int(reg["nivel"]) - 1, 0) if reg["nivel"] else "  "
            dom = milhar(int(reg["domicilios"])) if pd.notna(reg["domicilios"]) else "—"
            largura = 58 - len(recuo)
            partes = textwrap.wrap(nome, largura) or [""]
            for parte in partes[:-1]:
                linhas.append(f"{recuo}{parte}")
            linhas.append(
                f"{recuo}{partes[-1]:<{largura}}{dom:>10}{numero(reg['percentual'], 2) + '%':>10}"
            )
    return "\n".join(linhas) + "\n"


def secao_sinisa(indicadores: dict[str, tuple[pd.DataFrame, dict]] | None) -> str:
    """
    Formata os indicadores do SINISA do município.

    indicadores mapeia 'agua' e 'esgoto' ao par (tabela, meta) de
    carregadores.carregar_sinisa; None quando os relatórios não estão disponíveis.
    """
    linhas = [titulo("19. PRESTAÇÃO DOS SERVIÇOS — SINISA")]
    if not indicadores:
        linhas.append("  Relatórios do SINISA não disponíveis nesta execução.\n")
        return "\n".join(linhas)

    linhas.append(
        "Fonte: Ministério das Cidades, SINISA. Informações declaradas pelos\n"
        "prestadores e pelo município. O SINISA substituiu o SNIS a partir da\n"
        "coleta de 2024, ano de referência 2023 (Nota Informativa SEI/MIDR\n"
        "nº 5886717, de 02/07/2025); os indicadores não formam série com o SNIS.\n"
    )
    nomes = {"agua": "Abastecimento de água", "esgoto": "Esgotamento sanitário"}
    for chave, (tabela, meta) in indicadores.items():
        linhas.append(
            subtitulo(f"{nomes.get(chave, chave)} — ano de referência {meta.get('ano_referencia')}")
        )
        for _, reg in tabela.iterrows():
            valor = numero(reg["valor"], 2) if pd.notna(reg["valor"]) else "—"
            partes = textwrap.wrap(str(reg["indicador"]), 52) or [""]
            linhas.append(f"  {reg['codigo']:<9}{partes[0]:<53}{valor:>10} {reg['unidade']}")
            linhas.extend(f"  {'':<9}{parte}" for parte in partes[1:])
    return "\n".join(linhas) + "\n"


def secao_plano_amostragem(plano: pd.DataFrame) -> str:
    """Formata o cumprimento do plano de amostragem do Vigiagua."""
    linhas = [titulo("20. CUMPRIMENTO DO PLANO DE AMOSTRAGEM (VIGIAGUA)")]
    if plano.empty:
        linhas.append("  Sem dados.\n")
        return "\n".join(linhas)

    regra = "para cima" if config.PLANO_AMOSTRAGEM_ARREDONDAMENTO == "cima" else "para baixo"
    linhas.append(
        "Mínimo mensal pela Diretriz Nacional do Plano de Amostragem\n"
        "(Ministério da Saúde, 2016), pela população de cada ano.\n"
        f"Parcela variável arredondada {regra}; conferir no plano municipal.\n"
        "Fluoreto faz parte do plano básico, mas não está nos arquivos\n"
        "do SISAGUA usados aqui.\n\n"
        "O mínimo da Diretriz é mensal. A coluna % compara o total do ano\n"
        "com o total exigido e pode passar de 100% mesmo com meses abaixo\n"
        "do mínimo; o cumprimento mensal está na coluna 'c/ mínimo'.\n"
        "Sensib. = meses que atingiriam o mínimo com arredondamento para\n"
        "baixo (valor do mínimo entre parênteses), até a regra ser confirmada.\n"
    )

    for parametro, bloco in plano.groupby("parametro", sort=False):
        linhas.append(subtitulo(str(parametro)))
        linhas.append(
            f"  {'Ano':<6}{'Mín./mês':>9}{'Meses':>7}{'c/ coleta':>11}"
            f"{'c/ mínimo':>11}{'Amostras':>10}{'Exigido':>9}{'%':>8}"
            f"{'Sensib.':>10}"
        )
        for _, reg in bloco.iterrows():
            sensib = f"{int(reg['meses_minimo_baixo'])} (≥{int(reg['minimo_mensal_baixo'])})"
            linhas.append(
                f"  {int(reg['ano']):<6}{int(reg['minimo_mensal']):>9}"
                f"{int(reg['meses_periodo']):>7}{int(reg['meses_com_coleta']):>11}"
                f"{int(reg['meses_minimo_atingido']):>11}{int(reg['amostras']):>10}"
                f"{int(reg['minimo_total']):>9}{numero(reg['percentual_cumprido']) + '%':>8}"
                f"{sensib:>10}"
            )
        sem_coleta = [
            f"{int(reg['ano'])}: "
            + ", ".join(config.MESES_ABREV[m] for m in reg["meses_sem_coleta"])
            for _, reg in bloco.iterrows()
            if reg["meses_sem_coleta"]
        ]
        if sem_coleta:
            linhas.append("\n  Meses sem nenhuma coleta:")
            linhas.extend(f"    {t}" for t in sem_coleta)

    return "\n".join(linhas) + "\n"
