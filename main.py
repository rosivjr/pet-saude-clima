"""
Gera o relatório de agravos relacionados à água e da qualidade da água.

Carrega SIH, SINAN, SIM, CNES, SISAGUA, Censo 2022, SINISA e a chuva do
Open-Meteo; padroniza, filtra e calcula os indicadores; escreve o relatório
em texto no stdout (o log vai para o stderr), as figuras em figuras/ e o
JSON de proveniência da execução.
"""

import logging
import sys
from dataclasses import dataclass

import pandas as pd
import pandera.errors

from src import config, graficos, proveniencia, qualidade, relatorio
from src.carregadores import (
    carregar_censo_sidra,
    carregar_cnes_periodo,
    carregar_populacao_abastecida,
    carregar_precipitacao,
    carregar_sih,
    carregar_sim,
    carregar_sinan,
    carregar_sinisa,
    carregar_sisagua,
)
from src.indicadores import (
    avaliar_conformidade_agua,
    avaliar_microbiologico,
    capacidade_hospitalar,
    cobertura_censo,
    composicao_cadastro_por_ano,
    conferir_subcategorias,
    conformidade_por_area,
    cruzar_notificacoes_internacoes,
    cumprimento_plano_amostragem,
    divergencia_desinfeccao,
    ecoli_por_area,
    ecoli_por_captacao,
    ecoli_por_ponto,
    indicador_drsai,
    local_de_internacao,
    mortalidade_por_faixa,
    mortalidade_por_grupo,
    notificacoes_por_ano,
    perfil_abastecimento,
    perfil_etario,
    perfil_etario_feco_oral,
    perfil_notificacoes,
    perfil_por_grupo,
    perfil_rede,
    precipitacao_mensal,
    rede_do_ano,
    residentes_fora_do_para,
    resumo_cloro_areas,
    sazonalidade_comparada,
    sazonalidade_ecoli,
    sensibilidade_sem_ano_parcial,
    serie_anual_agua,
    serie_anual_internacoes,
    serie_anual_mortalidade,
    serie_anual_todas_causas,
    serie_mensal,
    serie_mensal_internacoes,
    serie_rede_por_ano,
)
from src.transformacoes import (
    filtrar_agravos,
    filtrar_aih_normal,
    filtrar_drsai,
    filtrar_municipio_cnes,
    filtrar_municipio_sih,
    filtrar_periodo,
    padronizar_cnes,
    padronizar_populacao,
    padronizar_sih,
    padronizar_sim,
    padronizar_sinan,
    padronizar_sisagua,
)
from src.validacao import validar

logger = logging.getLogger(__name__)


def configurar_log() -> None:
    """
    Configura o formato e o destino das mensagens de log, a partir do nível INFO.

    O log vai para stderr e o relatório para stdout, permitindo redirecionar
    apenas o relatório para arquivo sem perder as mensagens de execução.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s %(name)-22s %(message)s",
        stream=sys.stderr,
    )


def preparar_internacoes():
    """
    Carrega e prepara os dados de internação hospitalar.

    Returns:
        Tupla com (1) todas as internações de residentes no período, AIH
        tipo 1, (2) o subconjunto classificado em algum grupo de agravo e
        (3) o subconjunto dos grupos do DRSAI.
    """
    df = padronizar_sih(carregar_sih())
    df = filtrar_municipio_sih(df)
    df = filtrar_aih_normal(df)
    todas = filtrar_periodo(df, "DT_INTER", fonte="SIH")
    agravos = filtrar_agravos(todas)
    return todas, agravos, filtrar_drsai(agravos)


def preparar_obitos():
    """
    Carrega e prepara os óbitos do SIM.

    Returns:
        Tupla com o SIM padronizado e filtrado no período e a lista de anos
        com arquivo carregado (base do denominador das taxas).
    """
    df = padronizar_sim(carregar_sim())
    anos = list(df.attrs.get("anos", []))
    if df.empty:
        return df, anos
    return filtrar_periodo(df, "DTOBITO", fonte="SIM"), anos


def preparar_notificacoes():
    """Carrega e prepara as notificações compulsórias."""
    df = padronizar_sinan(carregar_sinan())
    return df if df.empty else filtrar_periodo(df, "DT_NOTIFIC", fonte="SINAN")


def preparar_agua():
    """Carrega e prepara os dados de qualidade da água."""
    return filtrar_periodo(padronizar_sisagua(carregar_sisagua()), "DT_COLETA", fonte="SISAGUA")


def preparar_cadastro():
    """Cadastro de soluções de abastecimento padronizado, uma linha por solução e ano."""
    return padronizar_populacao(carregar_populacao_abastecida())


def preparar_rede():
    """CNES do município, uma competência por ano, com a coluna competencia_ano."""
    return filtrar_municipio_cnes(padronizar_cnes(carregar_cnes_periodo()))


def preparar_perfil_sanitario():
    """
    Carrega Censo 2022 e SINISA, arquivos baixados manualmente.

    Um arquivo ausente ou fora do formato esperado não interrompe o
    relatório: a seção correspondente informa que o dado não está
    disponível, e a falha fica na proveniência.

    Returns:
        Tupla (coberturas do Censo, indicadores do SINISA), cada uma um
        dicionário possivelmente vazio.
    """
    coberturas, sinisa = {}, {}
    for chave in config.CENSO_2022_TABELAS:
        try:
            coberturas[chave] = cobertura_censo(
                carregar_censo_sidra(chave),
                config.CENSO_2022_SUBCATEGORIAS.get(chave),
            )
            divergentes = conferir_subcategorias(coberturas[chave])
            if divergentes:
                logger.warning("Censo 2022 (%s): subcategorias não somam %s", chave, divergentes)
        except (FileNotFoundError, ValueError) as erro:
            logger.warning("Censo 2022 (%s) indisponível: %s", chave, erro)
    for chave in config.SINISA_ARQUIVOS:
        try:
            sinisa[chave] = carregar_sinisa(chave)
        except (FileNotFoundError, ValueError) as erro:
            logger.warning("SINISA (%s) indisponível: %s", chave, erro)
    return coberturas, sinisa


def _rodapes_figuras() -> dict[str, str]:
    """Rodapé de cada fonte das figuras, com a data de extração desta execução."""
    local = f"{config.MUNICIPIO_NOME} ({config.MUNICIPIO_UF})"
    return {
        "agua": relatorio.rodape_figura(
            f"SISAGUA, vigilância da qualidade da água, {local}",
            proveniencia.datas_de_extracao("SISAGUA"),
            criterio=f"{config.CRITERIO_PORTARIA_888}. Unidade: amostra de água.",
        ),
        "internacoes": relatorio.rodape_figura(
            f"SIH/SUS, internações de residentes em {local}, por data de internação",
            proveniencia.datas_de_extracao("SIH"),
        ),
        "hospitais": relatorio.rodape_figura(
            f"CNES (leitos) e SIH/SUS (internações de residentes), {local}",
            proveniencia.datas_de_extracao("CNES", "SIH"),
        ),
    }


@dataclass
class Bases:
    """Bases padronizadas e filtradas de uma execução."""

    todas: pd.DataFrame  # internações de residentes no período, todas as causas
    internacoes: pd.DataFrame  # classificadas em algum grupo de agravo
    internacoes_drsai: pd.DataFrame
    notificacoes: pd.DataFrame
    obitos: pd.DataFrame
    anos_sim: list[int]  # anos com arquivo do SIM carregado
    agua: pd.DataFrame
    cadastro: pd.DataFrame
    rede: pd.DataFrame
    coberturas: dict
    sinisa: dict


def carregar_bases() -> Bases:
    """Carrega, padroniza e filtra todas as bases, na ordem do relatório."""
    todas, internacoes, internacoes_drsai = preparar_internacoes()
    notificacoes = preparar_notificacoes()
    obitos, anos_sim = preparar_obitos()
    agua = preparar_agua()
    cadastro = preparar_cadastro()
    rede = preparar_rede()
    coberturas, sinisa = preparar_perfil_sanitario()
    return Bases(
        todas,
        internacoes,
        internacoes_drsai,
        notificacoes,
        obitos,
        anos_sim,
        agua,
        cadastro,
        rede,
        coberturas,
        sinisa,
    )


def validar_bases(bases: Bases) -> None:
    """Validação estrutural: para a execução se alguma base mudou de formato."""
    validar("SIH", bases.todas)
    validar("SINAN", bases.notificacoes)
    validar("SIM", bases.obitos)
    validar("SISAGUA", bases.agua)
    validar("SISAGUA cadastro", bases.cadastro)
    validar("CNES", bases.rede)


def carregar_chuva() -> pd.DataFrame | None:
    """Precipitação diária; sem ela, a seção de chuva diz que o dado falta."""
    try:
        return carregar_precipitacao()
    except RuntimeError as erro:
        logger.warning("Precipitação indisponível: %s", erro)
        return None


def indicadores_saude(bases: Bases) -> dict:
    """Internações e notificações por grupo, idade e mês; cruzamento e limitação do SIH."""
    internacoes, notificacoes = bases.internacoes, bases.notificacoes
    etario, excluidos = perfil_etario(internacoes)
    etario_feco, excl_feco = perfil_etario_feco_oral(internacoes)
    return {
        "drsai": indicador_drsai(internacoes),
        "perfis": perfil_por_grupo(internacoes),
        "etario": etario,
        "excluidos": excluidos,
        "serie_int": serie_mensal_internacoes(internacoes),
        "notif": perfil_notificacoes(notificacoes),
        "notif_ano": notificacoes_por_ano(notificacoes),
        "cobertura": cruzar_notificacoes_internacoes(notificacoes, internacoes),
        "etario_feco": etario_feco,
        "excl_feco": excl_feco,
        "fora_do_para": residentes_fora_do_para(),
    }


def indicadores_agua(bases: Bases) -> dict:
    """Conformidade, microbiologia, cloro por área, E. coli por área, captação e ponto."""
    agua = bases.agua
    cloro_area = conformidade_por_area(agua)
    return {
        "conformidade": avaliar_conformidade_agua(agua),
        "microbiologico": avaliar_microbiologico(agua),
        "serie_cloro": serie_mensal(agua, config.PARAMETRO_CLORO),
        "cloro_area": cloro_area,
        "ecoli_area": ecoli_por_area(agua),
        "captacao": ecoli_por_captacao(agua, bases.cadastro),
        "por_ponto": ecoli_por_ponto(agua),
        "sazonal": sazonalidade_ecoli(agua),
        "resumo_cloro": resumo_cloro_areas(cloro_area),
    }


def indicadores_abastecimento(bases: Bases) -> dict:
    """Infraestrutura de abastecimento do cadastro do SISAGUA."""
    return {
        "abastecimento": perfil_abastecimento(bases.cadastro),
        "composicao": composicao_cadastro_por_ano(bases.cadastro),
        "divergencia": divergencia_desinfeccao(bases.cadastro, bases.agua),
    }


def indicadores_rede(bases: Bases) -> dict:
    """Rede de atenção e local das internações por DRSAI (escopo do Eixo II)."""
    rede_atual = rede_do_ano(bases.rede)
    return {
        "ano_rede": (int(rede_atual["competencia_ano"].iloc[0]) if not rede_atual.empty else None),
        "perfil_da_rede": perfil_rede(rede_atual),
        # Local de internação: estabelecimentos do município em qualquer ano.
        "local_internacao": local_de_internacao(bases.internacoes_drsai, bases.rede),
        "hospitais": capacidade_hospitalar(rede_atual, bases.internacoes_drsai),
        "serie_rede": serie_rede_por_ano(bases.rede),
    }


def indicadores_series_e_qualidade(bases: Bases) -> dict:
    """Séries anuais, plano de amostragem, mortalidade, qualidade dos dados e sensibilidade."""
    b = bases
    return {
        "anual_int": serie_anual_internacoes(b.internacoes),
        "anual_todas": serie_anual_todas_causas(b.todas, b.internacoes),
        "anual_agua": serie_anual_agua(b.agua),
        "plano": cumprimento_plano_amostragem(b.agua),
        "mortes_grupo": mortalidade_por_grupo(b.obitos, b.anos_sim),
        "mortes_ano": serie_anual_mortalidade(b.obitos, b.anos_sim),
        "mortes_faixa": mortalidade_por_faixa(b.obitos),
        "completitude": qualidade.completitude(b.todas, b.notificacoes, b.obitos, b.agua),
        "consistencia": qualidade.consistencia(b.todas, b.notificacoes, b.agua),
        "duplicidade": qualidade.duplicidade(b.todas, b.notificacoes),
        "sensibilidade": sensibilidade_sem_ano_parcial(b.internacoes, b.agua),
    }


def indicadores_chuva(precipitacao: pd.DataFrame | None, r: dict) -> dict:
    """Chuva mensal e a comparação com E. coli e internações, se houver chuva."""
    if precipitacao is None:
        return {"chuva_mensal": None, "comparada": None, "meta_chuva": None}
    chuva_mensal = precipitacao_mensal(precipitacao)
    return {
        "chuva_mensal": chuva_mensal,
        "comparada": sazonalidade_comparada(chuva_mensal, r["sazonal"], r["serie_int"]),
        "meta_chuva": precipitacao.attrs.get("meta"),
    }


def calcular_indicadores(bases: Bases, precipitacao: pd.DataFrame | None) -> dict:
    """Todos os resultados usados nas figuras e no relatório, por nome."""
    r = indicadores_saude(bases)
    r |= indicadores_agua(bases)
    r |= indicadores_abastecimento(bases)
    r |= indicadores_rede(bases)
    r |= indicadores_series_e_qualidade(bases)
    r |= indicadores_chuva(precipitacao, r)
    return r


def gerar_figuras(r: dict) -> None:
    """Figuras em figuras/, a partir dos resultados já calculados."""
    graficos.gerar_todos(
        r["conformidade"],
        r["microbiologico"],
        r["ecoli_area"],
        r["sazonal"],
        r["perfis"],
        r["hospitais"],
        r["etario"],
        r["etario_feco"],
        r["serie_cloro"],
        r["captacao"],
        _rodapes_figuras(),
    )


def imprimir_relatorio(r: dict, bases: Bases, resumo_prov: dict, caminho_proveniencia) -> None:
    """Escreve o relatório no stdout, seção por seção."""
    secoes = [
        relatorio.cabecalho(),
        relatorio.secao_drsai(r["drsai"]),
        relatorio.secao_perfil_grupos(r["perfis"]),
        relatorio.secao_perfil_etario(r["etario"], r["excluidos"]),
        relatorio.secao_serie_internacoes(r["serie_int"]),
        relatorio.secao_notificacoes(r["notif"], r["notif_ano"]),
        relatorio.secao_cobertura_fontes(r["cobertura"]),
        relatorio.secao_lacunas(resumo_prov["indisponiveis"]),
        relatorio.secao_conformidade(r["conformidade"]),
        relatorio.secao_microbiologica(r["microbiologico"]),
        relatorio.secao_serie_agua(r["serie_cloro"], "Cloro residual livre"),
        relatorio.secao_territorial(r["cloro_area"], r["ecoli_area"], r["resumo_cloro"]),
        relatorio.secao_abastecimento(r["abastecimento"], r["composicao"], r["divergencia"]),
        relatorio.secao_rede(
            r["perfil_da_rede"],
            r["local_internacao"],
            r["hospitais"],
            r["serie_rede"],
            r["ano_rede"],
        ),
        relatorio.secao_ecoli(r["captacao"], r["por_ponto"], r["sazonal"]),
        relatorio.secao_etario_feco_oral(r["etario_feco"], r["excl_feco"]),
        relatorio.secao_serie_anual_internacoes(r["anual_int"], r["anual_todas"]),
        relatorio.secao_serie_anual_agua(r["anual_agua"]),
        relatorio.secao_censo(bases.coberturas),
        relatorio.secao_sinisa(bases.sinisa),
        relatorio.secao_plano_amostragem(r["plano"]),
        relatorio.secao_precipitacao(r["comparada"], r["chuva_mensal"], r["meta_chuva"]),
        relatorio.secao_mortalidade(
            r["mortes_grupo"], r["mortes_ano"], r["mortes_faixa"], bases.anos_sim
        ),
        relatorio.secao_qualidade(r["completitude"], r["consistencia"], r["duplicidade"]),
        relatorio.secao_sensibilidade(r["sensibilidade"]),
        relatorio.secao_proveniencia(resumo_prov, caminho_proveniencia),
        relatorio.rodape(r["fora_do_para"]),
    ]
    for secao in secoes:
        print(secao)


def registrar_falha_de_validacao(erro: pandera.errors.SchemaErrors) -> None:
    """
    Loga só a contagem de falhas por coluna e checagem.

    failure_cases traz os valores e o índice de cada registro reprovado,
    que não podem ir para o log.
    """
    contagem = erro.failure_cases.groupby(["column", "check"], dropna=False).size().rename("falhas")
    logger.error(
        "Validação estrutural falhou; a execução foi interrompida para não "
        "gerar números com uma base fora do formato esperado. Falhas por "
        "coluna e checagem:\n%s",
        contagem.to_string(),
    )


def executar() -> int:
    """
    Executa o pipeline completo de análise.

    Returns:
        Código de saída: 0 em sucesso, 1 em falha prevista (validação,
        dado ausente, falha de carga). Erro inesperado não é capturado:
        mostra o traceback e o Python sai com código 1, sem gravar a
        proveniência.
    """
    proveniencia.reiniciar()
    try:
        bases = carregar_bases()
        validar_bases(bases)
        resultados = calcular_indicadores(bases, carregar_chuva())
        # Gravada antes do relatório, que cita o arquivo.
        caminho_proveniencia = proveniencia.salvar()
        resumo_prov = proveniencia.resumo()
        gerar_figuras(resultados)
        imprimir_relatorio(resultados, bases, resumo_prov, caminho_proveniencia)
        return 0
    except pandera.errors.SchemaErrors as erro:
        registrar_falha_de_validacao(erro)
    except FileNotFoundError as erro:
        logger.error("Dado ausente: %s", erro)
    except RuntimeError as erro:
        logger.error("Falha ao carregar dados: %s", erro)
    proveniencia.salvar()
    return 1


if __name__ == "__main__":
    configurar_log()
    sys.exit(executar())
