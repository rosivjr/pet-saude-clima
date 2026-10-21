"""Seção do cadastro de soluções de abastecimento e da desinfecção declarada."""

import pandas as pd

from src.indicadores import PerfilAbastecimento

from ._formato import ic, milhar, numero, subtitulo, titulo


def secao_abastecimento(
    perfil: PerfilAbastecimento,
    composicao: pd.DataFrame,
    divergencia: dict,
) -> str:
    """Formata o cadastro de soluções de abastecimento e o cloro medido."""
    linhas = [titulo("12. SOLUÇÕES DE ABASTECIMENTO CADASTRADAS")]
    linhas.append(
        "Fonte: SISAGUA, cadastro de população abastecida (autodeclarado\n"
        "pelos responsáveis pelas soluções).\n"
    )

    if not composicao.empty:
        linhas.append(subtitulo("Cadastro por ano"))
        linhas.append(
            f"  {'Ano':<6}{'Soluções':>10}{'SAA':>6}{'SAC':>6}{'SAI':>6}"
            f"{'Desinfecção':>13}{'Pop. somada':>14}"
        )
        for _, reg in composicao.iterrows():
            pop = milhar(int(reg["populacao_estimada"]))
            linhas.append(
                f"  {int(reg['ano']):<6}{int(reg['solucoes']):>10}{int(reg['SAA']):>6}"
                f"{int(reg['SAC']):>6}{int(reg['SAI']):>6}"
                f"{int(reg['declaram_desinfeccao']):>13}{pop:>14}"
            )
        linhas.append(
            "\n  Desinfecção = soluções que declaram ter desinfecção.\n"
            "  Pop. somada = soma da população declarada por solução; a mesma\n"
            "  pessoa pode estar em mais de uma solução, então não é cobertura.\n"
            "  O cadastro do ano corrente pode estar em atualização."
        )

    if perfil.total_solucoes == 0:
        linhas.append("\n  Sem soluções cadastradas no período.\n")
        return "\n".join(linhas)

    linhas.append(
        subtitulo(f"Composição no cadastro de {perfil.ano_referencia} (último ano completo)")
    )
    nomes_tipo = {
        "SAA": "Sistema de Abastecimento de Água (rede formal)",
        "SAC": "Solução Alternativa Coletiva",
        "SAI": "Solução Alternativa Individual",
    }
    linhas.append(f"  Total de soluções ....... {perfil.total_solucoes}\n")
    for sigla, quantidade in sorted(perfil.por_tipo.items(), key=lambda x: x[1], reverse=True):
        linhas.append(
            f"  {nomes_tipo.get(sigla, sigla)}\n"
            f"    {quantidade} soluções ({numero(perfil.percentual_por_tipo[sigla])}%)\n"
        )
    linhas.append(
        f"  Declaram desinfecção .... {perfil.declaram_desinfeccao} "
        f"de {perfil.total_solucoes}\n"
        f"  Declaram filtração ...... {perfil.declaram_filtracao} "
        f"de {perfil.total_solucoes}\n"
        f"  Captação subterrânea .... {perfil.captacao_subterranea} "
        f"de {perfil.total_solucoes}\n"
    )

    if divergencia and divergencia.get("amostras_avaliadas"):
        linhas.append(
            subtitulo("Cloro medido nas soluções que declaram desinfecção (todo o período)")
        )
        linhas.append(
            "  Cada amostra foi ligada ao cadastro da solução no ano da coleta ou, se\n"
            "  não houver, no ano anterior mais próximo e, na falta dele, no seguinte\n"
            "  (decisão 0005).\n\n"
            f"  Soluções distintas com amostra ...... "
            f"{divergencia['solucoes_declarantes']}\n"
            f"  Amostras de cloro nessas soluções ... "
            f"{divergencia['amostras_avaliadas']}\n"
            f"  Abaixo do mínimo legal .............. "
            f"{divergencia['fora_do_padrao']} "
            f"({numero(divergencia['percentual_fora'])}%, "
            f"{ic(divergencia['ic_inferior'], divergencia['ic_superior'])})\n"
        )
        ligacao = divergencia.get("ligacao")
        if ligacao:
            linhas.append(
                "  Ligação das amostras de cloro ao cadastro da solução:\n"
                f"    mesmo ano ............. {ligacao['mesmo_ano']}\n"
                f"    ano anterior .......... {ligacao['ano_anterior']}\n"
                f"    ano seguinte .......... {ligacao['ano_seguinte']}\n"
                f"    sem cadastro .......... {ligacao['sem_par']} "
                f"(de {ligacao['solucoes_sem_par']} solução(ões))\n"
            )
        linhas.append(
            "  Ressalva: o campo de desinfecção é autodeclarado e não é\n"
            "  verificado em campo pelo sistema."
        )

    return "\n".join(linhas) + "\n"
