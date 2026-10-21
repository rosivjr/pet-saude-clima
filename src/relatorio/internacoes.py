"""Seções de internações do SIH: indicador DRSAI, perfis, faixa etária e séries."""

import pandas as pd

from src import config
from src.indicadores import PerfilAgravo

from ._formato import ic, numero, subtitulo, titulo

# Explicação de cada grupo que fica fora do indicador DRSAI.
DESCRICAO_FORA_DRSAI = {
    config.GRUPO_ARBOVIROSES_EXTRA: (
        "Arboviroses ausentes da lista FUNASA (2010), anterior à chegada\n"
        "de chikungunya e zika ao Brasil."
    ),
    config.GRUPO_SENSIBILIDADE: (
        "Códigos de listas locais que não constam da classificação FUNASA\n"
        "(A05, E86, L00-L08). Não somados ao indicador DRSAI."
    ),
    config.GRUPO_CONTEXTO_CLIMATICO: (
        "Agravos citados na contextualização do projeto: doenças respiratórias,\n"
        "por relação com período seco e queimadas, e acidentes por animais\n"
        "peçonhentos (T63)."
    ),
}


def secao_drsai(indicador: PerfilAgravo) -> str:
    """Formata o indicador agregado de internações por DRSAI."""
    linhas = [titulo("1. INTERNAÇÕES POR DRSAI — INDICADOR AGREGADO")]
    linhas.append(
        "Doenças Relacionadas ao Saneamento Ambiental Inadequado\n"
        "Classificação FUNASA (2010); indicador 33 dos Indicadores de\n"
        "Desenvolvimento Sustentável do IBGE (IDS Brasil 2015).\n"
    )
    linhas.append(
        f"  Internações ............. {indicador.internacoes}\n"
        f"  Taxa/100 mil pessoas-ano  {numero(indicador.taxa_100mil, 2)} "
        f"({ic(indicador.taxa_ic_inferior, indicador.taxa_ic_superior, 2)})\n"
        f"  Óbitos .................. {indicador.obitos}\n"
        f"  Letalidade .............. {numero(indicador.letalidade)}% "
        f"({ic(indicador.letalidade_ic_inferior, indicador.letalidade_ic_superior)})\n"
        f"  Permanência média ....... {numero(indicador.permanencia_media)} dias\n"
    )
    return "\n".join(linhas)


def _formatar_perfil(p: PerfilAgravo) -> str:
    """Formata um único perfil de agravo."""
    aviso = (
        ""
        if p.amostra_suficiente
        else f"\n    [!] menos de {config.LIMIAR_AMOSTRA_MINIMA} casos: estimativa instável"
    )
    return (
        f"  {p.grupo}\n"
        f"    Internações ........... {p.internacoes}\n"
        f"    Taxa/100 mil p-a ...... {numero(p.taxa_100mil, 2)} "
        f"({ic(p.taxa_ic_inferior, p.taxa_ic_superior, 2)})\n"
        f"    Óbitos ................ {p.obitos} "
        f"(letalidade {numero(p.letalidade)}%, "
        f"{ic(p.letalidade_ic_inferior, p.letalidade_ic_superior)})\n"
        f"    Permanência média ..... {numero(p.permanencia_media)} dias"
        f"{aviso}\n"
    )


def secao_perfil_grupos(perfis: list[PerfilAgravo]) -> str:
    """Formata o perfil de internações por grupo de agravo."""
    linhas = [titulo("2. INTERNAÇÕES POR GRUPO DE AGRAVO")]

    drsai = [p for p in perfis if p.grupo in config.GRUPOS_DRSAI]
    outros = [p for p in perfis if p.grupo not in config.GRUPOS_DRSAI]

    linhas.append(subtitulo("Grupos DRSAI (escopo do Eixo II)"))
    for p in drsai:
        linhas.append(_formatar_perfil(p))

    if outros:
        linhas.append(subtitulo(config.ROTULO_FORA_DRSAI))
        for p in outros:
            descricao = DESCRICAO_FORA_DRSAI.get(p.grupo)
            if descricao:
                linhas.append(f"  ({descricao.replace(chr(10), ' ')})")
            linhas.append(_formatar_perfil(p))

    return "\n".join(linhas)


def _tabela_etaria(resumo: pd.DataFrame) -> list[str]:
    """Linhas da distribuição etária: faixa, internações, percentual e IC de Wilson."""
    linhas = [f"  {'Faixa':<10}{'Internações':>14}{'Percentual':>14}  IC95%", f"  {'-' * 52}"]
    for _, reg in resumo.iterrows():
        linhas.append(
            f"  {str(reg['faixa_etaria']):<10}"
            f"{int(reg['internacoes']):>14}"
            f"{numero(reg['percentual']) + '%':>14}  "
            f"{numero(reg['ic_inferior'])}–{numero(reg['ic_superior'])}%"
        )
    return linhas


def secao_perfil_etario(resumo: pd.DataFrame, excluidos: int) -> str:
    """Formata a distribuição etária das internações por DRSAI."""
    linhas = [titulo("3. DISTRIBUIÇÃO ETÁRIA — INTERNAÇÕES POR DRSAI")]

    if resumo.empty:
        linhas.append("  Sem dados de idade válidos.\n")
        return "\n".join(linhas)

    linhas.extend(_tabela_etaria(resumo))

    if excluidos:
        linhas.append(
            f"\n  Nota: {excluidos} internações sem idade válida, fora desta\n"
            f"  distribuição. Menores de 1 ano estão na faixa <1."
        )

    return "\n".join(linhas) + "\n"


def secao_serie_internacoes(serie: pd.DataFrame) -> str:
    """Formata a série mensal de internações por DRSAI."""
    linhas = [titulo("4. SÉRIE MENSAL — INTERNAÇÕES POR DRSAI")]

    if serie.empty:
        linhas.append("  Sem dados disponíveis.\n")
        return "\n".join(linhas)

    linhas.append(f"  {'Ano':<8}{'Mês':<8}{'Internações':>14}")
    linhas.append(f"  {'-' * 30}")

    for _, reg in serie.iterrows():
        linhas.append(
            f"  {int(reg['ano']):<8}{config.MESES_ABREV[int(reg['mes'])]:<8}"
            f"{int(reg['internacoes']):>14}"
        )

    return "\n".join(linhas) + "\n"


def secao_etario_feco_oral(resumo: pd.DataFrame, excluidos: int) -> str:
    """Formata a distribuição etária específica do grupo feco-oral."""
    linhas = [titulo("15. DISTRIBUIÇÃO ETÁRIA — AGRAVOS FECO-ORAIS")]
    linhas.append("Recorte das internações do grupo feco-oral por faixa etária.\n")

    if resumo.empty:
        linhas.append("  Sem dados de idade válidos.\n")
        return "\n".join(linhas)

    linhas.extend(_tabela_etaria(resumo))

    if excluidos:
        linhas.append(f"\n  Nota: {excluidos} internações sem idade válida.")

    return "\n".join(linhas) + "\n"


def _faixa_meses(meses: list[int]) -> str:
    """Rótulo dos meses comuns: 'jan–jun', ou a lista se não forem seguidos."""
    if not meses:
        return "nenhum"
    if meses == list(range(meses[0], meses[-1] + 1)):
        return f"{config.MESES_ABREV[meses[0]]}–{config.MESES_ABREV[meses[-1]]}"
    return ", ".join(config.MESES_ABREV[m] for m in meses)


def _rotulo_ano(reg) -> str:
    """Ano com asterisco quando é parcial."""
    return f"{int(reg['ano'])}{'*' if reg.get('ano_parcial') else ''}"


def _rt_texto(reg, primeiro: int, sem_casos: str) -> tuple[str, str]:
    """RT e seu IC formatados; 'ref.' no ano de referência."""
    if int(reg["ano"]) == primeiro:
        return "ref.", ""
    if pd.isna(reg["razao_taxas"]):
        return "—", sem_casos
    return (
        numero(reg["razao_taxas"], 2),
        f"{numero(reg['rt_ic_inferior'], 2)}–{numero(reg['rt_ic_superior'], 2)}",
    )


def secao_serie_anual_internacoes(
    serie: pd.DataFrame,
    todas_causas: pd.DataFrame | None = None,
) -> str:
    """
    Formata a taxa anual de internação com IC e razão de taxas.

    Mostra duas tabelas por indicador: a taxa anualizada de cada ano, só
    como descrição, com o ano parcial marcado, e a comparação entre anos
    nos meses comuns (decisão 0008), que é a que leva a razão de taxas.
    Inclui o total de internações por todas as causas e a proporção
    DRSAI/total, para separar variação do grupo de variação do registro.
    """
    linhas = [titulo("16. SÉRIE ANUAL — INTERNAÇÕES POR DRSAI")]

    if serie.empty:
        linhas.append("  Dados insuficientes.\n")
        return "\n".join(linhas)

    primeiro = int(serie["ano"].min())
    meses = _faixa_meses(serie.attrs.get("meses_comuns", []))
    linhas.append(
        "Taxa por 100 mil pessoas-ano. A taxa anualizada de cada ano é só\n"
        "descrição (decisão 0008); o ano parcial (*) usa a pessoa-tempo do\n"
        "trecho coberto.\n"
        f"A comparação entre anos usa só os meses comuns a todos os anos ({meses}),\n"
        f"decisão 0008. RT = razão de taxas nesses meses em relação a {primeiro}.\n"
        "Os meses finais do ano parcial ainda recebem AIH com atraso e podem\n"
        "crescer nas próximas extrações.\n"
    )

    for indicador, bloco in serie.groupby("indicador", sort=False):
        linhas.append(subtitulo(str(indicador)))
        linhas.append("  Taxa anualizada (descrição)")
        linhas.append(f"  {'Ano':<6}{'n':>6}{'Taxa':>10}  IC95%")
        for _, reg in bloco.iterrows():
            ic_taxa = f"{numero(reg['taxa_ic_inferior'], 2)}–{numero(reg['taxa_ic_superior'], 2)}"
            linhas.append(
                f"  {_rotulo_ano(reg):<6}{int(reg['internacoes']):>6}"
                f"{numero(reg['taxa'], 2):>10}  {ic_taxa}"
            )
        linhas.append(f"\n  Meses comuns, {meses} (comparação)")
        linhas.append(f"  {'Ano':<6}{'n':>6}{'Taxa':>10}  {'IC95%':<17}{'RT':>6}  IC95% RT")
        for _, reg in bloco.iterrows():
            ic_taxa = (
                f"{numero(reg['taxa_mc_ic_inferior'], 2)}–{numero(reg['taxa_mc_ic_superior'], 2)}"
            )
            rt, ic_rt = _rt_texto(reg, primeiro, "(sem casos)")
            linhas.append(
                f"  {_rotulo_ano(reg):<6}{int(reg['internacoes_mc']):>6}"
                f"{numero(reg['taxa_mc'], 2):>10}  {ic_taxa:<17}{rt:>6}  {ic_rt}".rstrip()
            )

    if todas_causas is not None and not todas_causas.empty:
        linhas.append(subtitulo("Referência: internações de residentes por todas as causas"))
        linhas.append(
            "  Se o total geral cresce junto, parte da variação das DRSAI\n"
            "  acompanha o volume de internações. Se a proporção DRSAI/total\n"
            "  muda, a variação não acompanha só o volume de internações.\n"
        )
        linhas.append(f"  Taxa anualizada; RT nos meses comuns ({meses}).")
        linhas.append(
            f"  {'Ano':<6}{'Total':>8}{'Taxa':>10}  {'IC95%':<17}"
            f"{'n ' + meses:>12}{'RT':>6}  IC95% RT"
        )
        for _, reg in todas_causas.iterrows():
            ic_taxa = f"{numero(reg['taxa_ic_inferior'])}–{numero(reg['taxa_ic_superior'])}"
            rt, ic_rt = _rt_texto(reg, primeiro, "")
            linhas.append(
                f"  {_rotulo_ano(reg):<6}{int(reg['total']):>8}{numero(reg['taxa']):>10}  "
                f"{ic_taxa:<17}{int(reg['total_mc']):>12}{rt:>6}  {ic_rt}".rstrip()
            )

        linhas.append(f"\n  {'Ano':<6}{'DRSAI':>8}{'DRSAI/total':>14}  IC95%")
        for _, reg in todas_causas.iterrows():
            linhas.append(
                f"  {int(reg['ano']):<6}{int(reg['drsai']):>8}"
                f"{numero(reg['proporcao_drsai'], 2) + '%':>14}  "
                f"{numero(reg['prop_ic_inferior'], 2)}–{numero(reg['prop_ic_superior'], 2)}%"
            )

    return "\n".join(linhas) + "\n"
