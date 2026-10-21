"""Cabeçalho, lacunas, qualidade dos dados, proveniência e rodapé do relatório."""

import os
import textwrap

import pandas as pd

from src import config

from ._formato import LARGURA, data, extracao, ic, milhar, numero, subtitulo, titulo


def cabecalho() -> str:
    """Monta o cabeçalho do relatório com escopo, população e fontes."""
    linhas_pop = "\n".join(
        f"  {ano} ....... {milhar(pop)} hab. ({config.POPULACAO_FONTE[ano]})"
        for ano, pop in config.POPULACAO_ANUAL.items()
    )
    tema, programa = config.TITULO_PROJETO.split(" — ")
    return (
        f"{titulo(tema.upper())}\n"
        f"{programa}\n\n"
        f"Município ................ {config.MUNICIPIO_NOME} ({config.MUNICIPIO_UF})\n"
        f"Código IBGE .............. {config.MUNICIPIO_IBGE_7}\n"
        f"Período .................. {data(config.PERIODO_INICIO)} a "
        f"{data(config.PERIODO_FIM)}\n\n"
        f"População de referência (denominador em pessoas-ano):\n"
        f"{linhas_pop}\n\n"
        f"Taxas por 100 mil pessoas-ano, com IC 95% exato de Poisson (Garwood).\n"
        f"Proporções com IC 95% de Wilson.\n\n"
        f"Fontes, todas de acesso público:\n"
        f"  SIH/SUS ........... internações (DATASUS, via PySUS)\n"
        f"  SINAN ............. notificações compulsórias (DATASUS, via PySUS)\n"
        f"  SIM ............... óbitos (DATASUS, via PySUS)\n"
        f"  CNES .............. estabelecimentos de saúde (DATASUS, via PySUS)\n"
        f"  SISAGUA ........... vigilância da água e cadastro de abastecimento\n"
        f"                      (Portal de Dados Abertos)\n"
        f"  SINISA ............ prestação dos serviços de saneamento\n"
        f"                      (Ministério das Cidades)\n"
        f"  Censo 2022 ........ saneamento dos domicílios (IBGE, SIDRA)\n"
        f"  Precipitação ...... chuva diária por reanálise (Open-Meteo)\n"
    )


def secao_lacunas(indisponiveis: list[dict] | None = None) -> str:
    """
    Formata as lacunas: estruturais (do config) e desta execução.

    indisponiveis é a lista proveniencia.resumo()["indisponiveis"].
    """
    linhas = [titulo("7. LACUNAS DE DADOS")]
    linhas.append(subtitulo("Estruturais (não dependem do ano baixado)"))
    for agravo, motivo in config.SINAN_LACUNAS.items():
        linhas.append(f"  {agravo}\n    {motivo}\n")

    dentro, depois = _separar_por_periodo(indisponiveis or [])

    linhas.append(subtitulo("Arquivos indisponíveis nesta execução"))
    if not dentro:
        linhas.append("  Nenhum.\n")
    else:
        for item in dentro:
            linhas.append(f"  {item['fonte']:<18}{item['item']:<22}{item['motivo']}")
        linhas.append("")

    ano, mes = config.SIH_ULTIMA_COMPETENCIA
    corte = f"  SIH extraído até a competência {ano}-{mes:02d}"
    if depois:
        corte += " (indisponíveis: " + ", ".join(i["item"].split()[1] for i in depois) + ")"
    linhas.append(corte + "\n")

    return "\n".join(linhas)


def _separar_por_periodo(indisponiveis: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Separa competências do SIH posteriores ao fim do período das demais.

    Com o corte em config.SIH_ULTIMA_COMPETENCIA, as de depois do fim só
    aparecem aqui se uma competência até o corte não vier.

    Itens do SIH têm o formato 'UF AAAA-MM RD'.
    """
    fim = (config.PERIODO_FIM.year, config.PERIODO_FIM.month)
    dentro, depois = [], []
    for item in indisponiveis:
        partes = item["item"].split()
        if item["fonte"] == "SIH" and len(partes) >= 2 and "-" in partes[1]:
            ano, mes = (int(x) for x in partes[1].split("-"))
            if (ano, mes) > fim:
                depois.append(item)
                continue
        dentro.append(item)
    return dentro, depois


def secao_qualidade(
    completitude: pd.DataFrame,
    consistencia: pd.DataFrame,
    duplicidade: pd.DataFrame,
) -> str:
    """Formata as tabelas de completitude, consistência e duplicidade de qualidade.py."""
    linhas = [titulo("23. QUALIDADE DOS DADOS")]
    linhas.append(
        "Completitude pela escala de incompletude de Romero e Cunha (2006):\n"
        "excelente < 5%; bom 5 a 9,9%; regular 10 a 19,9%; ruim 20 a 49,9%;\n"
        "muito ruim >= 50%. Incompleto = campo em branco ou ignorado.\n"
        "Nenhum registro é removido por esta avaliação.\n"
    )

    linhas.append(subtitulo("Completitude"))
    linhas.append(f"  {'Base':<9}{'Campo':<44}{'Registros':>10}{'Incompl.':>10}  Classificação")
    for _, reg in completitude.iterrows():
        linhas.append(
            f"  {reg['base']:<9}{str(reg['campo'])[:43]:<44}{int(reg['registros']):>10}"
            f"{numero(reg['incompletude']) + '%':>10}  {reg['classificacao']}"
        )
    if (completitude["campo"] == "Classificação final*").any():
        *inicio, ultimo = [nome.lower() for nome in config.SINAN_SEM_CLASSI_FIN]
        sem_campo = f"{', '.join(inicio)} e {ultimo}" if inicio else ultimo
        linhas.append(f"\n  * Sem {sem_campo},\n    cujos arquivos não trazem o campo.")

    linhas.append(subtitulo("Consistência"))
    linhas.append(f"  {'Base':<9}{'Regra':<46}{'Avaliados':>10}{'Inconsist.':>12}")
    for _, reg in consistencia.iterrows():
        linhas.append(
            f"  {reg['base']:<9}{reg['regra']:<46}{int(reg['avaliados']):>10}"
            f"{int(reg['inconsistentes']):>12}"
        )

    linhas.append(subtitulo("Duplicidade"))
    for _, reg in duplicidade.iterrows():
        linhas.append(
            f"  {reg['base']:<9}{reg['criterio']:<46}{int(reg['registros']):>10}"
            f"{int(reg['repetidos']):>12}"
        )
    linhas.append(
        "\n  No SINAN, os dados públicos não têm identificação pessoal; a\n"
        "  duplicidade é estimada e não substitui o roteiro do Ministério da\n"
        "  Saúde, que usa nome e data de nascimento."
    )
    return "\n".join(linhas) + "\n"


def secao_proveniencia(resumo: dict, caminho_json) -> str:
    """
    Formata proveniencia.resumo() e aponta o JSON com o registro completo.

    O caminho do JSON aparece relativo à raiz do repositório, para o
    relatório não expor a pasta pessoal de quem o gerou.
    """
    caminho = os.path.relpath(caminho_json, config.RAIZ).replace(os.sep, "/")
    linhas = [titulo("25. PROVENIÊNCIA DESTA EXECUÇÃO")]
    linhas.append(
        f"  Início .................. {resumo['inicio']}\n"
        f"  PySUS ................... {resumo['pysus']} (source={resumo['pysus_source']})\n"
        f"  Registro completo ....... {caminho}\n"
    )

    linhas.append(subtitulo("Arquivos lidos por fonte"))
    for fonte, n in sorted(resumo["arquivos_por_fonte"].items()):
        linhas.append(f"  {fonte:<24}{n:>6}")

    linhas.append(subtitulo("Data de extração por fonte"))
    for fonte in sorted(resumo["arquivos_por_fonte"]):
        linhas.append(f"  {fonte:<18}{extracao(resumo['extracao'].get(fonte))}")
    linhas.append(
        "\n  Data do download registrada na proveniência; sem ela, a data de\n"
        "  modificação do arquivo, que muda quando o arquivo é copiado."
    )

    linhas.append(subtitulo("Todas as etapas de filtro, inclusive as que removeram 0 linhas"))
    linhas.append(
        "  Descarte: registro inválido ou fora da regra de limpeza.\n"
        "  Recorte: registro válido fora do escopo do estudo (período,\n"
        "  município, grupo de agravo); não é perda de dado.\n"
    )
    if not resumo["etapas"]:
        linhas.append("  Nenhuma etapa registrada.")
    else:
        linhas.append(f"  {'Etapa':<24}{'Tipo':<10}{'Antes':>10}{'Depois':>10}{'Removidas':>11}")
        for e in resumo["etapas"]:
            linhas.append(
                f"  {e['etapa']:<24}{e['tipo']:<10}{e['antes']:>10}{e['depois']:>10}"
                f"{e['antes'] - e['depois']:>11}\n"
                f"    {e['motivo']}"
            )

    linhas.append(
        "\n  O JSON guarda nome, tamanho, data, SHA-256, origem e data do\n"
        "  download de cada arquivo.\n"
        "  Resultados diferentes entre execuções podem ser rastreados\n"
        "  comparando esses registros."
    )
    return "\n".join(linhas) + "\n"


def rodape_figura(
    fonte: str,
    datas_extracao: tuple | None,
    periodo: str | None = None,
    criterio: str | None = None,
) -> str:
    """
    Texto de fonte, período e data de extração sob uma figura.

    Args:
        fonte: sistema e recorte geográfico, ex.: 'SIH/SUS, Parauapebas (PA)'.
        datas_extracao: proveniencia.datas_de_extracao(), formatada por extracao.
        periodo: período coberto; sem ele, o período do estudo no config.
        criterio: norma ou unidade dos valores, numa segunda linha.
    """
    if periodo is None:
        periodo = f"{data(config.PERIODO_INICIO)} a {data(config.PERIODO_FIM)}"
    texto = f"Fonte: {fonte}, {periodo}; {extracao(datas_extracao)}."
    return f"{texto}\nCritério: {criterio}" if criterio else texto


def _ressalva_fora_do_para(fora_do_para: pd.DataFrame | None) -> str:
    """Item das internações de residentes em outras UFs, com o tamanho medido."""
    if fora_do_para is None or fora_do_para.empty:
        return ""
    # Espaço não separável dentro do parêntese, para a quebra não separar o IC
    # dos números; volta a ser espaço comum depois do fill.
    medidas = " e ".join(
        f"{milhar(int(reg['fora']))} de {milhar(int(reg['total']))} em {int(reg['ano'])} "
        + f"({numero(reg['percentual'])}%; {ic(reg['ic_inferior'], reg['ic_superior'])})".replace(
            " ", "\xa0"
        )
        for _, reg in fora_do_para.iterrows()
    )
    texto = (
        "O SIH foi lido só nos arquivos do Pará: internações de residentes em "
        f"hospitais de outras UFs ficam fora. Medido à parte: {medidas}."
    )
    item = textwrap.fill(texto, width=LARGURA - 4, subsequent_indent="    ")
    return "  - " + item.replace("\xa0", " ") + "\n"


def rodape(fora_do_para: pd.DataFrame | None = None) -> str:
    """
    Monta o rodapé com as ressalvas metodológicas e lacunas conhecidas.

    fora_do_para é indicadores.residentes_fora_do_para(); sem ele, o item
    das internações em outras UFs não aparece.
    """
    return (
        f"{titulo('RESSALVAS METODOLÓGICAS')}"
        "\nQuanto às fontes\n"
        f"{'-' * LARGURA}\n"
        "  - Microdados públicos anonimizados, mostrados só em agregados; não\n"
        "    substituem a análise oficial da vigilância municipal.\n"
        "  - O SIH cobre apenas internações financiadas pelo SUS. Atendimentos\n"
        "    resolvidos na atenção primária ou em pronto atendimento não\n"
        "    aparecem, assim como internações na rede privada não conveniada.\n"
        "  - O SIH organiza os arquivos por competência de faturamento; o\n"
        "    recorte temporal foi feito pela data de internação (DT_INTER).\n"
        f"{_ressalva_fora_do_para(fora_do_para)}"
        "  - O SINAN registra apenas agravos de notificação compulsória.\n"
        "    Diarreias comuns e infecções de pele não são notificáveis, e a\n"
        "    ausência de registro não indica ausência de casos.\n"
        "  - A amostragem do SISAGUA reflete os pontos monitorados pelo setor\n"
        "    saúde, não necessariamente toda a rede de abastecimento.\n"
        "  - O cadastro de soluções de abastecimento é autodeclarado pelos\n"
        "    responsáveis e não é verificado em campo. A infraestrutura\n"
        "    declarada pode divergir da situação real.\n"
        "  - O CNES é um cadastro mensal substitutivo; cada ano é representado\n"
        "    por uma competência (mesmo mês), não pela média do ano.\n"
        "  - Meses sem registro podem indicar ausência de coleta ou atraso de\n"
        "    digitação na fonte.\n"
        "  - O Censo 2022 descreve os domicílios na data de referência do\n"
        f"    censo, não a situação de {min(config.ANOS)} a {max(config.ANOS)}.\n"
        "  - Os indicadores do SINISA são declarados pelos prestadores e pelo\n"
        "    município e não formam série com os do SNIS.\n"
        "\nQuanto à interpretação\n"
        f"{'-' * LARGURA}\n"
        "  - A coincidência temporal entre indicadores de água e agravos não\n"
        "    estabelece relação causal. O desenho é descritivo.\n"
        f"  - Grupos com menos de {config.LIMIAR_AMOSTRA_MINIMA} casos levam o aviso\n"
        f'    "menos de {config.LIMIAR_AMOSTRA_MINIMA} casos: estimativa instável".\n'
        f"  - Percentuais de amostras de água com menos de {config.LIMIAR_AMOSTRAS_PROPORCAO}"
        " amostras levam [!].\n"
        "  - Taxas usam pessoa-tempo: a população de cada ano multiplicada\n"
        "    pela fração do ano coberta pelo período.\n"
        "  - A população de 2023 foi obtida por interpolação geométrica entre\n"
        "    o Censo 2022 e a estimativa IBGE 2024; não é estimativa oficial.\n"
        "  - Intervalos de confiança de amostras de água tratam cada amostra\n"
        "    como independente. Coletas repetidas na mesma solução ou área não\n"
        "    são independentes, então os intervalos subestimam a incerteza.\n"
        "  - A classificação por idade converte dias e meses em menor de 1 ano\n"
        "    e o código de 100 anos ou mais em 100 + valor.\n"
        "  - Dados de internação do ano corrente estão sujeitos a\n"
        "    subestimação por atraso de faturamento e envio das AIH. Quedas\n"
        "    observadas no ano mais recente podem refletir dado incompleto,\n"
        "    não redução real de casos.\n"
        "\nLacunas conhecidas em relação às metas do Eixo II\n"
        f"{'-' * LARGURA}\n"
        "  - A distribuição territorial dos agravos (internações e notificações\n"
        "    por bairro) exige dado do e-SUS municipal. A distribuição da\n"
        "    qualidade da água por área está disponível e consta da seção 11.\n"
        "  - Tempo entre atendimento na atenção primária e atendimento\n"
        "    especializado exige integração com dados de regulação.\n"
        "  - Proporção de atendimentos com registro adequado em prontuário\n"
        "    exige acesso ao e-SUS APS.\n"
    )
