"""Seção da rede de saúde do CNES e do local de internação dos residentes."""

import pandas as pd

from src import config
from src.indicadores import PerfilRede

from ._formato import ic, numero, subtitulo, titulo


def secao_rede(
    perfil: PerfilRede,
    local: dict,
    hospitais: pd.DataFrame | None = None,
    serie_rede: pd.DataFrame | None = None,
    ano_rede: int | None = None,
) -> str:
    """
    Formata a rede de saúde e o local das internações por DRSAI.

    ano_rede é a competência da composição e dos hospitais (padrão:
    config.CNES_COMPETENCIA_ANO).
    """
    ano_rede = ano_rede or config.CNES_COMPETENCIA_ANO
    linhas = [titulo("13. REDE DE ATENÇÃO À SAÚDE")]
    linhas.append(
        "Fonte: CNES, Cadastro Nacional de Estabelecimentos de Saúde.\n"
        f"Uma competência por ano, sempre em {config.CNES_COMPETENCIA_MES:02d}.\n"
        f"Composição e hospitais: competência {config.CNES_COMPETENCIA_MES:02d}/{ano_rede}.\n"
    )

    if serie_rede is not None and not serie_rede.empty:
        linhas.append(subtitulo("Rede do município por ano"))
        linhas.append(
            f"  {'Ano':<6}{'Estab.':>8}{'SUS':>6}{'Hosp. gerais SUS':>18}"
            f"{'Leitos':>8}{'SUS c/ urgência':>17}"
        )
        for _, reg in serie_rede.iterrows():
            linhas.append(
                f"  {int(reg['ano']):<6}{int(reg['estabelecimentos']):>8}"
                f"{int(reg['vinculo_sus']):>6}{int(reg['hospitais_gerais_sus']):>18}"
                f"{int(reg['leitos_hospitais_gerais_sus']):>8}{int(reg['sus_com_urgencia']):>17}"
            )
        linhas.append("")

    if perfil.total == 0:
        linhas.append("  Sem estabelecimentos cadastrados.\n")
        return "\n".join(linhas)

    linhas.append(subtitulo("Composição da rede"))
    linhas.append(
        f"  Estabelecimentos cadastrados ... {perfil.total}\n"
        f"  Com vínculo SUS ................ {perfil.vinculados_sus} "
        f"({numero(perfil.percentual_sus)}%)\n"
        f"  Sem vínculo SUS ................ "
        f"{perfil.total - perfil.vinculados_sus} "
        f"({numero(perfil.percentual_sem_sus)}%)\n"
    )

    linhas.append(subtitulo("Rede SUS por tipo de unidade"))
    largura = max((len(t) for t in perfil.por_tipo_sus), default=0) + 2
    for tipo, quantidade in perfil.por_tipo_sus.items():
        linhas.append(f"  {tipo:<{largura}}{quantidade:>4}")

    linhas.append(
        f"\n  Com leitos hospitalares ........ {perfil.com_leitos}\n"
        f"  Com urgência e emergência ...... {perfil.com_urgencia}\n"
    )

    if hospitais is not None and not hospitais.empty:
        linhas.append(subtitulo("Hospitais gerais SUS e internações por DRSAI"))
        linhas.append(f"  {'Hospital':<42}{'Leitos':>8}{'Urg.':>7}{'Intern.':>9}")
        linhas.append(f"  {'-' * 66}")
        for _, reg in hospitais.iterrows():
            linhas.append(
                f"  {str(reg['nome'])[:41]:<42}"
                f"{int(reg['leitos']):>8}"
                f"{str(reg['urgencia']):>7}"
                f"{int(reg['internacoes']):>9}"
            )
        linhas.append(f"  {'-' * 66}")
        linhas.append(f"  {'Total de leitos':<42}{int(hospitais['leitos'].sum()):>8}\n")
        linhas.append("  Leitos: soma de QTLEITP1 a QTLEITP3 no CNES.")

    if not local:
        return "\n".join(linhas) + "\n"

    linhas.append(subtitulo("Local das internações por DRSAI dos residentes"))
    linhas.append(
        f"  Internações analisadas ......... {local['total']}\n"
        f"  Em estabelecimento do município  {local['dentro']} "
        f"({numero(local['percentual_dentro'])}%, {ic(*local['ic_dentro'])})\n"
        f"  Fora do município .............. {local['fora']} "
        f"({numero(local['percentual_fora'])}%, {ic(*local['ic_fora'])})\n"
        f"  Estabelecimentos distintos ..... {local['estabelecimentos_distintos']}\n"
    )

    nome = config.CNES_NOMES.get(local["principal_cnes"])
    linhas.append(subtitulo("Estabelecimento com mais internações"))
    if nome:
        linhas.append(f"  {nome}\n  (CNES {local['principal_cnes']})\n")
    else:
        linhas.append(f"  Estabelecimento CNES {local['principal_cnes']}\n")
    linhas.append(
        f"  Internações .................... {local['principal_internacoes']} "
        f"({numero(local['principal_percentual'])}% do total, {ic(*local['ic_principal'])})\n"
    )
    if local.get("principal_leitos"):
        linhas.append(f"  Leitos cadastrados ............. {local['principal_leitos']}\n")

    linhas.append(
        "  Estabelecimentos sem vínculo SUS não geram AIH; atendimentos\n"
        "  neles não aparecem no SIH nem nesta seção."
    )

    return "\n".join(linhas) + "\n"
