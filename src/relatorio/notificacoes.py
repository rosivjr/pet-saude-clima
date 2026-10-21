"""Seções de notificações do SINAN e da presença de cada grupo no SINAN e no SIH."""

import pandas as pd

from src import config
from src.indicadores import CruzamentoFontes

from ._formato import ic, numero, subtitulo, titulo


def _bloco_agravo_sinan(reg) -> str:
    """Contagens, taxa do período e máximo possível de um agravo do SINAN."""
    instavel = (
        ""
        if reg["amostra_suficiente"]
        else f"    [!] menos de {config.LIMIAR_AMOSTRA_MINIMA} casos: estimativa instável\n"
    )
    taxa = (
        f"    Taxa/100 mil p-a ...... {numero(reg['taxa_100mil'], 2)} "
        f"({ic(reg['taxa_ic_inferior'], reg['taxa_ic_superior'], 2)})\n{instavel}"
    )
    cabeca = f"  {reg['agravo']} ({reg['grupo_agravo']})\n"

    if not reg["tem_classi_fin"]:
        return (
            cabeca + f"    Notificados ........... {int(reg['notificacoes'])} "
            "(ficha sem CLASSI_FIN; casos = notificações)\n" + taxa
        )

    texto = (
        cabeca + f"    Notificados ........... {int(reg['notificacoes'])}\n"
        f"    Confirmados ........... {int(reg['confirmados'])}\n"
        f"    Descartados ........... {int(reg['descartados'])}\n"
        f"    Sem classificação ..... {int(reg['sem_classificacao'])}\n"
    )
    if reg["outros_codigos"]:
        texto += (
            f"    Outros códigos ........ {int(reg['outros_codigos'])} (fora da lista conferida)\n"
        )
    texto += taxa + (
        f"    Máximo possível ....... {int(reg['casos_maximo'])} "
        f"{'caso' if int(reg['casos_maximo']) == 1 else 'casos'}, "
        f"{numero(reg['taxa_maximo'], 2)} "
        f"({ic(reg['maximo_ic_inferior'], reg['maximo_ic_superior'], 2)})\n"
    )
    if reg["a_conferir"]:
        texto += (
            "    Ressalva: código de CLASSI_FIN de ficha estadual, a conferir\n"
            "    no dicionário nacional.\n"
        )
    return texto


def secao_notificacoes(resumo: pd.DataFrame, por_ano: pd.DataFrame | None = None) -> str:
    """Formata a seção de notificações compulsórias do SINAN (decisão 0001)."""
    linhas = [titulo("5. NOTIFICAÇÕES COMPULSÓRIAS (SINAN)")]

    if resumo.empty:
        linhas.append("  Nenhuma notificação registrada no período.\n")
        return "\n".join(linhas)

    linhas.append(
        "Agravos de notificação compulsória relacionados à água e ao clima.\n"
        "Complementa o SIH ao captar casos que não geraram internação.\n"
        "Caso = notificação com classificação final de confirmado (decisão\n"
        "0001). Agravos sem CLASSI_FIN na ficha são contados pelas notificações.\n"
        "Máximo possível = confirmados + sem classificação (sensibilidade).\n"
        "A taxa é do período inteiro; por ano, só contagens.\n"
    )

    drsai = resumo[resumo["grupo_agravo"].isin(config.GRUPOS_DRSAI)]
    outros = resumo[~resumo["grupo_agravo"].isin(config.GRUPOS_DRSAI)]

    if not drsai.empty:
        linhas.append(subtitulo("Agravos relacionados à água (grupos DRSAI)"))
        linhas += [_bloco_agravo_sinan(reg) for _, reg in drsai.iterrows()]

    if not outros.empty:
        linhas.append(subtitulo(config.ROTULO_FORA_DRSAI))
        linhas += [_bloco_agravo_sinan(reg) for _, reg in outros.iterrows()]

    if por_ano is not None and not por_ano.empty:
        linhas.append(subtitulo("Contagens por ano"))
        linhas.append(
            f"  {'Agravo':<32}{'Ano':<6}{'Notif.':>7}{'Conf.':>7}{'Desc.':>7}{'Sem cl.':>9}"
        )
        for _, reg in por_ano.iterrows():
            if reg["tem_classi_fin"]:
                conf, desc, sem = (
                    str(int(reg[c])) for c in ("confirmados", "descartados", "sem_classificacao")
                )
            else:
                conf = desc = sem = "—"
            linhas.append(
                f"  {str(reg['agravo'])[:31]:<32}{int(reg['ano']):<6}"
                f"{int(reg['notificacoes']):>7}{conf:>7}{desc:>7}{sem:>9}"
            )
        linhas.append(
            "\n  — = ficha sem CLASSI_FIN. Contagens pequenas: não calcular taxa por ano."
        )

    return "\n".join(linhas) + "\n"


def secao_cobertura_fontes(cruzamentos: list[CruzamentoFontes]) -> str:
    """Formata a comparação de cobertura entre SINAN e SIH."""
    linhas = [titulo("6. COBERTURA POR FONTE DE DADO")]
    linhas.append(
        "As duas fontes captam universos distintos e não são comparáveis\n"
        "por divisão: o SINAN registra apenas agravos de notificação\n"
        "compulsória; o SIH classifica todas as internações por CID-10.\n"
        "Casos = notificações confirmadas; nos agravos sem CLASSI_FIN,\n"
        "as notificações (decisão 0001).\n"
    )

    linhas.append(f"  {'Grupo':<28}{'Notificações':>14}{'Casos':>8}{'Internações':>14}")
    linhas.append(f"  {'-' * 64}")

    for c in cruzamentos:
        linhas.append(f"  {c.grupo[:27]:<28}{c.notificacoes:>14}{c.casos:>8}{c.internacoes:>14}")

    linhas.append("")
    for c in cruzamentos:
        linhas.append(f"  {c.grupo}\n    {c.leitura}\n")

    return "\n".join(linhas)
