"""
Leitura das fontes, sem filtrar conteúdo.

SIH, SINAN, SIM e CNES vêm pelo PySUS, lidos do cache local quando o
arquivo já foi baixado (sem consultar o servidor); SISAGUA, Censo 2022 (SIDRA) e
SINISA, de arquivos baixados à mão para data/raw/; a chuva, da API do
Open-Meteo. CSVs grandes são lidos em blocos, com o filtro de município
aplicado durante a leitura.

Cada arquivo lido é anotado em src/proveniencia.py (nome, tamanho, data,
SHA-256, origem e data do download), e cada arquivo esperado que não pôde
ser obtido fica registrado como indisponível.
"""

import json
import logging
import re
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as pads
import requests
from pysus import ftp as pysus_ftp
from pysus.api.errors import PySUSError

from src import config, proveniencia

# Falhas esperadas ao baixar pelo PySUS: erros do próprio PySUS, inclusive
# parâmetro recusado (ValidationError), e de rede/FTP (OSError).
ERROS_PYSUS = (PySUSError, OSError)
# Falhas esperadas ao ler um parquet: arquivo ausente ou corrompido.
ERROS_LEITURA = (OSError, ValueError, pa.ArrowException)

# Como um arquivo do PySUS foi obtido nesta execução (campo leitura da proveniência).
LEITURA_CACHE = "cache local do PySUS, sem consulta ao servidor"
LEITURA_SERVIDOR = "PySUS, com consulta ao servidor"

logger = logging.getLogger(__name__)


def _ler_csv_filtrado(
    caminho: Path,
    separador: str,
    colunas: tuple[str, ...],
    coluna_filtro: str,
    valor_filtro: int | str,
    fonte: str,
    tamanho_bloco: int = 500_000,
) -> pd.DataFrame:
    """
    Lê um CSV grande em blocos, mantendo apenas as linhas que casam com o filtro.

    Cada bloco é lido, filtrado e descartado antes do próximo, então o
    arquivo inteiro nunca fica na memória. O resultado é o mesmo de ler tudo
    e filtrar depois; muda só o uso de memória (limite de 24 GB de RAM).
    O arquivo fica na proveniência com o nome do sistema dado em fonte.

    Raises:
        FileNotFoundError: se o arquivo não existir.
    """
    if not caminho.exists():
        proveniencia.registrar_indisponivel(fonte, caminho.name, "arquivo ausente")
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}\n"
            f"Baixe o dataset e salve nesse caminho antes de executar."
        )

    logger.info("Lendo %s em blocos de %d linhas", caminho.name, tamanho_bloco)

    blocos_filtrados = []
    total_lido = 0

    leitor = pd.read_csv(
        caminho,
        sep=separador,
        encoding="latin1",
        usecols=colunas,
        chunksize=tamanho_bloco,
        low_memory=False,
    )

    for bloco in leitor:
        total_lido += len(bloco)
        blocos_filtrados.append(bloco[bloco[coluna_filtro] == valor_filtro])

    df = pd.concat(blocos_filtrados, ignore_index=True)
    logger.info(
        "%s: %d linhas lidas, %d mantidas após filtro",
        caminho.name,
        total_lido,
        len(df),
    )
    proveniencia.registrar_arquivo(
        fonte, caminho, f"{total_lido} linhas lidas, {len(df)} do município"
    )
    return df


def _colunas_do_parquet(caminho: str) -> list[str]:
    """Nomes das colunas de um Parquet (arquivo ou pasta), sem ler os dados."""
    return pads.dataset(caminho, format="parquet").schema.names


def _ler_parquet(
    caminho: str, colunas: list[str] | tuple[str, ...]
) -> tuple[pd.DataFrame, set[str]]:
    """
    Lê apenas as colunas pedidas que existem no arquivo.

    Returns:
        Tupla com o DataFrame e o conjunto de colunas pedidas e ausentes.
    """
    existentes = _colunas_do_parquet(caminho)
    presentes = [c for c in colunas if c in existentes]
    ausentes = set(colunas) - set(presentes)
    return pd.read_parquet(caminho, columns=presentes), ausentes


def _origem_pysus(sistema: str, **parametros) -> str:
    """Endereço da origem do PySUS e a consulta que identifica o arquivo."""
    consulta = ", ".join(f"{k}={v}" for k, v in parametros.items())
    return f"{config.PYSUS_ENDERECOS[config.PYSUS_SOURCE]}; pysus.ftp.{sistema}({consulta})"


def _registrar_pysus(
    fonte: str, sistema: str, caminho: str, descricao: str, leitura: str, **parametros
) -> None:
    """
    Anota um arquivo do PySUS com a origem, a data do download e a leitura.

    O PySUS grava o arquivo no cache local quando o baixa e o reaproveita
    depois; a data de modificação do arquivo é, portanto, a do download, e
    não a da leitura.
    """
    proveniencia.registrar_arquivo(
        fonte,
        caminho,
        descricao,
        origem=_origem_pysus(sistema, **parametros),
        baixado_em=proveniencia.data_do_arquivo(caminho),
        leitura=leitura,
    )


def _do_cache(sistema: str, nome: str) -> str | None:
    """
    Caminho do arquivo no cache local do PySUS, se ele já foi baixado.

    Toda chamada ao PySUS consulta o catálogo remoto, mesmo com o arquivo no
    cache: lista os arquivos e compara o tamanho do local com o do remoto.
    Lendo direto do cache, a execução não depende do servidor e repete os
    mesmos arquivos; o que falta no cache ainda vem pelo PySUS. Dados
    preliminares só se atualizam pelos alvos make baixar-* (docs/dados.md).
    """
    caminho = config.PYSUS_PASTA_CACHE / sistema / nome
    return str(caminho) if caminho.exists() else None


def _baixar(funcao, prefixo: str, descricao: str, **parametros) -> str | None:
    """
    Baixa um conjunto pelo PySUS e devolve o arquivo cujo nome começa com o prefixo.

    Tenta primeiro com group=prefixo, que evita baixar os outros subconjuntos
    (SP, RJ, ER no SIH; LT, EQ etc. no CNES). Se nada vier, tenta sem group.

    Args:
        funcao: fetcher de pysus.ftp (sih, cnes).
        prefixo: início do nome do arquivo desejado ("RD", "ST").
        descricao: rótulo para log e proveniência.
        **parametros: argumentos do fetcher (state, year, month).
    """
    for extra in ({"group": prefixo}, {}):
        # TypeError só na tentativa com group=: fetcher que não aceita o parâmetro.
        esperados = (*ERROS_PYSUS, TypeError) if extra else ERROS_PYSUS
        try:
            caminhos = funcao(**parametros, **extra, source=config.PYSUS_SOURCE)
        except esperados as erro:
            logger.info("%s: tentativa com %s falhou (%s)", descricao, extra, type(erro).__name__)
            continue
        escolhido = next(
            (c for c in caminhos or [] if Path(c).name.upper().startswith(prefixo)), None
        )
        if escolhido:
            return escolhido
    return None


def _obter(funcao, sistema: str, nome: str, descricao: str, **parametros) -> tuple[str | None, str]:
    """
    Arquivo do cache local, ou baixado pelo PySUS se não estiver lá.

    Returns:
        Caminho (None se não houver) e a leitura, para a proveniência.
    """
    caminho = _do_cache(sistema, nome)
    if caminho:
        return caminho, LEITURA_CACHE
    return _baixar(funcao, nome[:2], descricao, **parametros), LEITURA_SERVIDOR


def carregar_sisagua() -> pd.DataFrame:
    """
    Carrega os dados de vigilância da qualidade da água (SISAGUA).

    Os arquivos originais somam vários GB, então a leitura é feita em blocos
    e o filtro de município é aplicado durante a leitura, mantendo em memória
    apenas os registros de interesse.

    Inclui campos territoriais (área de abrangência, tipo e nome do ponto de
    coleta), que permitem a análise por bairro exigida pela Meta 1 do Eixo II.

    Fonte: dadosabertos.saude.gov.br
    Dataset: SISAGUA - Vigilância Parâmetros Básicos

    Returns:
        DataFrame com os registros do município, de todos os anos configurados.

    Raises:
        FileNotFoundError: se algum arquivo de ano esperado não existir.
    """
    colunas = (
        "CO_MUNICIPIO_IBGE",
        "NO_MUNICIPIO",
        "NU_ANO",
        "NU_MES",
        "DT_COLETA",
        "TP_ABASTECIMENTO",
        "NU_SOLUCAO_ABASTECIMENTO",
        "TP_ZONA",
        "NO_AREA",  # bairro ou área de abrangência
        "NO_CATEGORIA_AREA",  # categoria da área
        "TP_PONTO_COLETA",  # torneira após reservação, bebedouro, etc.
        "TP_LOCAL",  # tipo de estabelecimento, quando informado
        "NO_LOCAL",  # nome do estabelecimento, quando informado
        "PARAMETRO",
        "RESULTADO",
    )

    quadros = []
    for ano in config.ANOS:
        caminho = config.DADOS_BRUTOS / f"sisagua_{ano}.csv"
        quadros.append(
            _ler_csv_filtrado(
                caminho=caminho,
                separador=";",
                colunas=colunas,
                coluna_filtro="CO_MUNICIPIO_IBGE",
                valor_filtro=config.MUNICIPIO_IBGE_6,
                fonte="SISAGUA",
            )
        )

    df = pd.concat(quadros, ignore_index=True)
    logger.info(
        "SISAGUA consolidado: %d registros do município %d",
        len(df),
        config.MUNICIPIO_IBGE_6,
    )
    return df


COLUNAS_SIH = (
    "N_AIH",  # identificador da internação
    "IDENT",  # tipo de AIH (1 = normal, 5 = longa permanência)
    "MUNIC_RES",  # município de residência do paciente
    "MUNIC_MOV",  # município do hospital
    "DIAG_PRINC",  # CID-10 do diagnóstico principal
    "DIAG_SECUN",  # CID-10 secundário
    "IDADE",
    "COD_IDADE",  # unidade da idade
    "SEXO",
    "DT_INTER",  # data da internação (AAAAMMDD)
    "DT_SAIDA",  # data da alta
    "DIAS_PERM",  # dias de permanência
    "MORTE",  # 1 = óbito
    "UTI_MES_TO",  # dias em UTI
    "CNES",  # estabelecimento
    "CAR_INT",  # caráter da internação (urgência/eletiva)
)


def carregar_sih(
    uf: str | None = None,
    anos: list[int] | None = None,
) -> pd.DataFrame:
    """
    Carrega as internações (SIH/SUS, AIH Reduzida) de residentes do município.

    Os arquivos são mensais por UF e organizados por competência de
    faturamento, não por data de internação; o recorte temporal final é
    feito depois, pela coluna DT_INTER. O filtro de residência é aplicado
    a cada mês, para não acumular a UF inteira na memória.

    Nenhuma competência depois de config.SIH_ULTIMA_COMPETENCIA é pedida ao
    PySUS: o corte é fixo para que o resultado não dependa do que o servidor
    já publicou. Ele muda só trocando a constante e rodando make baixar-sih
    (docs/dados.md).

    Fonte: DATASUS, via pysus.ftp.sih (subconjunto RD).

    Args:
        uf: sigla da UF. Se None, usa a do config.
        anos: anos de competência a baixar. Se None, usa os do config.

    Returns:
        DataFrame com as internações de residentes, todas as causas.

    Raises:
        RuntimeError: se nenhum arquivo puder ser carregado.
    """
    uf = uf or config.MUNICIPIO_UF
    anos = anos or config.ANOS

    quadros = []
    for ano in anos:
        for mes in range(1, 13):
            if (ano, mes) > config.SIH_ULTIMA_COMPETENCIA:
                break
            rotulo = f"{uf} {ano}-{mes:02d} RD"
            nome = f"RD{uf}{str(ano)[2:]}{mes:02d}.parquet"
            caminho, leitura = _obter(
                pysus_ftp.sih, "sih", nome, rotulo, state=uf, year=ano, month=mes
            )

            if caminho is None:
                proveniencia.registrar_indisponivel("SIH", rotulo, "sem arquivo RD")
                continue

            try:
                bloco, ausentes = _ler_parquet(caminho, COLUNAS_SIH)
            except ERROS_LEITURA as erro:
                logger.warning("%s: falha ao ler (%s)", rotulo, type(erro).__name__)
                proveniencia.registrar_indisponivel(
                    "SIH", rotulo, f"falha de leitura: {type(erro).__name__}"
                )
                continue

            if ausentes:
                logger.warning("%s: colunas ausentes %s", rotulo, sorted(ausentes))

            residentes = bloco[
                bloco["MUNIC_RES"].astype(str).str.strip() == config.MUNICIPIO_IBGE_6_STR
            ]
            quadros.append(residentes)
            _registrar_pysus(
                "SIH",
                "sih",
                caminho,
                f"{rotulo}: {len(bloco)} AIH na UF, {len(residentes)} de residentes",
                leitura,
                state=uf,
                year=ano,
                month=mes,
            )
            logger.info("SIH %s: %d de %d AIH de residentes", rotulo, len(residentes), len(bloco))

    if not quadros:
        raise RuntimeError(f"Nenhum dado do SIH carregado para {uf} em {anos}.")

    df = pd.concat(quadros, ignore_index=True)
    logger.info("SIH consolidado: %d internações de residentes", len(df))
    return df


COLUNAS_SINAN = (
    "ID_AGRAVO",
    "ID_MN_RESI",  # município de residência
    "DT_NOTIFIC",  # data da notificação
    "DT_SIN_PRI",  # data dos primeiros sintomas
    "NU_ANO",
    "NU_IDADE_N",
    "CS_SEXO",
    "CLASSI_FIN",  # classificação final (ausente em alguns agravos, ex.: ANIM)
    "EVOLUCAO",  # desfecho
)


def carregar_sinan(
    agravos: dict[str, tuple[str, str]] | None = None,
    anos: list[int] | None = None,
) -> pd.DataFrame:
    """
    Carrega notificações do SINAN de residentes, para os agravos do config.

    Os arquivos são nacionais; o filtro de residência é aplicado logo
    após a leitura. Combinações agravo/ano sem arquivo publicado ficam
    registradas como indisponíveis e aparecem no relatório.

    Fonte: DATASUS, via pysus.ftp.sinan.

    Args:
        agravos: mapa de código -> (nome, grupo). Se None, usa o do config.
        anos: anos a carregar. Se None, usa os do config.

    Returns:
        DataFrame com as notificações, com colunas 'agravo' e 'grupo_agravo'.
    """
    agravos = agravos or config.SINAN_AGRAVOS
    anos = anos or config.ANOS

    quadros = []
    for codigo, (nome, grupo) in agravos.items():
        for ano in anos:
            rotulo = f"{codigo} {ano}"
            no_cache = _do_cache("sinan", f"{codigo}BR{str(ano)[2:]}.parquet")
            leitura = LEITURA_CACHE if no_cache else LEITURA_SERVIDOR
            try:
                caminhos = (
                    [no_cache]
                    if no_cache
                    else pysus_ftp.sinan(disease=codigo, year=ano, source=config.PYSUS_SOURCE)
                )
            except ERROS_PYSUS as erro:
                proveniencia.registrar_indisponivel("SINAN", rotulo, type(erro).__name__)
                continue

            if not caminhos:
                proveniencia.registrar_indisponivel("SINAN", rotulo, "sem arquivo publicado")
                continue

            for caminho in caminhos:
                try:
                    bloco, ausentes = _ler_parquet(caminho, COLUNAS_SINAN)
                except ERROS_LEITURA as erro:
                    proveniencia.registrar_indisponivel(
                        "SINAN", rotulo, f"falha de leitura: {type(erro).__name__}"
                    )
                    continue

                if "ID_MN_RESI" not in bloco.columns:
                    proveniencia.registrar_indisponivel("SINAN", rotulo, "sem coluna ID_MN_RESI")
                    continue
                if ausentes:
                    logger.warning("%s: colunas ausentes %s", Path(caminho).name, sorted(ausentes))

                recorte = bloco[
                    bloco["ID_MN_RESI"].astype(str).str.strip() == config.MUNICIPIO_IBGE_6_STR
                ].copy()
                _registrar_pysus(
                    "SINAN",
                    "sinan",
                    caminho,
                    f"{rotulo}: {len(bloco)} no país, {len(recorte)} de residentes",
                    leitura,
                    disease=codigo,
                    year=ano,
                )
                if recorte.empty:
                    continue

                recorte["agravo"] = nome
                recorte["grupo_agravo"] = grupo
                quadros.append(recorte)
                logger.info("SINAN %s: %d notificações no município", rotulo, len(recorte))

    if not quadros:
        logger.warning("Nenhuma notificação do SINAN encontrada para o município")
        return pd.DataFrame(columns=list(COLUNAS_SINAN) + ["agravo", "grupo_agravo"])

    df = pd.concat(quadros, ignore_index=True)
    logger.info("SINAN consolidado: %d notificações", len(df))
    return df


def carregar_populacao_abastecida() -> pd.DataFrame:
    """
    Carrega o cadastro de soluções de abastecimento e população atendida.

    Complementa os dados de qualidade ao informar quantas pessoas cada
    solução abastece, se declara tratamento e qual a origem da água.

    Um único arquivo com todos os anos; o ano está na coluna NU_ANO.

    Fonte: dadosabertos.saude.gov.br
    Dataset: SISAGUA - População Abastecida

    Raises:
        FileNotFoundError: se o arquivo não existir.
    """
    colunas = (
        "CO_MUNICIPIO_IBGE",
        "NO_MUNICIPIO",
        "NU_ANO",
        "TP_ABASTECIMENTO",
        "NU_SOLUCAO_ABASTECIMENTO",  # chave de ligação com a qualidade
        "NO_SOLUCAO_ABASTECIMENTO",
        "NO_EMPRESA",
        "CAPTACAO_SUPERFICIAL",
        "CAPTACAO_SUBTERRANEA",
        "CAPTACAO_AGUA_CHUVA",
        "FILTRACAO",
        "DESINFECCAO",
        "NU_VALOR_POPULACAO_ESTIMADA",
        "NU_VALOR_RURAL",
        "NU_VALOR_URBANA",
    )

    caminho = config.DADOS_BRUTOS / "sisagua_populacao.csv"

    return _ler_csv_filtrado(
        caminho=caminho,
        separador=";",
        colunas=colunas,
        coluna_filtro="CO_MUNICIPIO_IBGE",
        valor_filtro=config.MUNICIPIO_IBGE_6,
        fonte="SISAGUA cadastro",
    )


COLUNAS_CNES = (
    "CNES",  # código do estabelecimento
    "CODUFMUN",  # município (6 dígitos)
    "TP_UNID",  # tipo de unidade
    "VINC_SUS",  # 1 = atende pelo SUS
    "LEITHOSP",  # 1 = possui leitos hospitalares
    "URGEMERG",  # 1 = possui urgência e emergência
    "ATENDAMB",  # atendimento ambulatorial
    "ATENDHOS",  # atendimento hospitalar
    "NIV_HIER",  # nível hierárquico
    "TPGESTAO",  # esfera de gestão
    "QTLEITP1",  # leitos
    "QTLEITP2",
    "QTLEITP3",
)


def carregar_cnes(ano: int | None = None, mes: int | None = None) -> pd.DataFrame:
    """
    Carrega o cadastro de estabelecimentos (CNES, subconjunto ST) de uma competência.

    Fonte: DATASUS, via pysus.ftp.cnes. Devolve os estabelecimentos da UF com
    a coluna competencia_ano. A UF é a do config, e ano e mês omitidos também vêm dele.

    Raises:
        RuntimeError: se o arquivo ST não puder ser carregado.
    """
    uf = config.MUNICIPIO_UF
    ano = ano or config.CNES_COMPETENCIA_ANO
    mes = mes or config.CNES_COMPETENCIA_MES
    rotulo = f"{uf} {ano}-{mes:02d} ST"

    nome = f"ST{uf}{str(ano)[2:]}{mes:02d}.parquet"
    caminho, leitura = _obter(pysus_ftp.cnes, "cnes", nome, rotulo, state=uf, year=ano, month=mes)
    if caminho is None:
        proveniencia.registrar_indisponivel("CNES", rotulo, "sem arquivo ST")
        raise RuntimeError(f"Subconjunto ST não encontrado para {rotulo}.")

    df, ausentes = _ler_parquet(caminho, COLUNAS_CNES)
    if ausentes:
        logger.warning("CNES %s: colunas ausentes %s", rotulo, sorted(ausentes))

    _registrar_pysus(
        "CNES",
        "cnes",
        caminho,
        f"{rotulo}: {len(df)} estabelecimentos",
        leitura,
        state=uf,
        year=ano,
        month=mes,
    )
    df["competencia_ano"] = ano
    logger.info("CNES %s: %d estabelecimentos", rotulo, len(df))
    return df


def carregar_cnes_periodo(
    anos: list[int] | None = None,
    mes: int | None = None,
) -> pd.DataFrame:
    """
    Carrega uma competência do CNES por ano, sempre no mesmo mês.

    Um ano sem competência publicada fica registrado como indisponível e
    não interrompe os demais.

    Args:
        anos: anos. Se None, usa config.ANOS.
        mes: mês da competência. Se None, usa config.CNES_COMPETENCIA_MES.

    Returns:
        DataFrame com todas as competências e a coluna competencia_ano.

    Raises:
        RuntimeError: se nenhuma competência puder ser carregada.
    """
    anos = anos or config.ANOS
    quadros = []
    for ano in anos:
        try:
            quadros.append(carregar_cnes(ano=ano, mes=mes))
        except RuntimeError as erro:
            logger.warning("%s", erro)

    if not quadros:
        raise RuntimeError(f"Nenhuma competência do CNES carregada para {anos}.")
    return pd.concat(quadros, ignore_index=True)


def _numero_sidra(texto: str) -> float:
    """Converte uma célula do SIDRA; '-', '...' e 'X' (sigilo) viram NaN."""
    texto = texto.strip()
    if texto in {"", "-", "...", "X", ".."}:
        return float("nan")
    return float(texto.replace(".", "").replace(",", "."))


def carregar_censo_sidra(chave: str) -> pd.DataFrame:
    """
    Lê um CSV exportado do SIDRA e devolve as contagens do município.

    O arquivo tem um bloco por variável (unidades e percentual). Só o
    primeiro bloco, de contagens, é usado; o percentual é recalculado.

    Args:
        chave: 'agua', 'esgoto' ou 'lixo' (config.CENSO_2022_TABELAS).

    Returns:
        DataFrame com as colunas categoria e domicilios, na ordem do arquivo.
        A primeira linha é o total.

    Raises:
        FileNotFoundError: se o arquivo não existir.
        ValueError: se o formato ou o município não forem encontrados.
    """
    nome, descricao = config.CENSO_2022_TABELAS[chave]
    caminho = config.DADOS_BRUTOS / nome
    codigo = str(config.MUNICIPIO_IBGE_7)

    if not caminho.exists():
        proveniencia.registrar_indisponivel("Censo 2022", nome, "arquivo ausente")
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    linhas = caminho.read_text(encoding="utf-8-sig").splitlines()
    campos = [[c.strip('"') for c in linha.split(";")] for linha in linhas]

    cabecalho = next(
        (
            i
            for i, c in enumerate(campos)
            if len(c) > 3 and c[:4] == ["Nível", "Cód.", "Município", "Total"]
        ),
        None,
    )
    if cabecalho is None:
        raise ValueError(f"{nome}: cabeçalho de categorias não encontrado")

    dados = next(
        (c for c in campos[cabecalho + 1 :] if len(c) > 1 and c[1] == codigo),
        None,
    )
    if dados is None:
        raise ValueError(f"{nome}: município {codigo} não encontrado no primeiro bloco")

    categorias = campos[cabecalho][3:]
    valores = [_numero_sidra(v) for v in dados[3 : 3 + len(categorias)]]

    proveniencia.registrar_arquivo("Censo 2022", caminho, descricao)
    return pd.DataFrame({"categoria": categorias, "domicilios": valores})


def carregar_sinisa(chave: str) -> tuple[pd.DataFrame, dict]:
    """
    Lê o relatório de indicadores do SINISA de um módulo.

    O relatório tem um cabeçalho de texto (título, ano de referência e
    município) e, abaixo da linha 'Código', uma linha por indicador. As
    colunas de valor e unidade podem vir deslocadas em relação ao
    cabeçalho; por isso o valor é o primeiro campo numérico depois do nome
    e a unidade, o primeiro texto depois do valor.

    Args:
        chave: 'agua' ou 'esgoto' (config.SINISA_ARQUIVOS).

    Returns:
        Tupla com (1) DataFrame com codigo, indicador, valor e unidade e
        (2) dicionário com ano_referencia e municipio lidos do cabeçalho.

    Raises:
        FileNotFoundError: se o arquivo não existir.
        ValueError: se a linha de cabeçalho 'Código' não for encontrada.
    """
    caminho = config.DADOS_BRUTOS / config.SINISA_ARQUIVOS[chave]
    if not caminho.exists():
        proveniencia.registrar_indisponivel("SINISA", caminho.name, "arquivo ausente")
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    bruto = pd.read_excel(caminho, header=None, dtype=str)
    textos = [str(v) for v in bruto.iloc[:5].to_numpy().ravel() if pd.notna(v)]

    meta = {"ano_referencia": None, "municipio": None}
    for t in textos:
        achado = re.search(r"refer[êe]ncia:\s*(\d{4})", t, flags=re.IGNORECASE)
        if achado:
            meta["ano_referencia"] = int(achado.group(1))
    if len(textos) >= 3:
        meta["municipio"] = textos[2].strip()

    inicio = next((i for i, v in enumerate(bruto[0]) if str(v).strip() == "Código"), None)
    if inicio is None:
        raise ValueError(f"{caminho.name}: linha 'Código' não encontrada")

    registros = []
    for _, linha in bruto.iloc[inicio + 1 :].iterrows():
        codigo = str(linha[0]).strip()
        if not re.fullmatch(r"I[A-Z]{2}\d{4}", codigo):
            continue
        resto = [str(v).strip() for v in linha[2:] if pd.notna(v) and str(v).strip()]
        valor, unidade = float("nan"), ""
        for i, v in enumerate(resto):
            try:
                valor = _numero_sidra(v)
            except ValueError:
                continue
            unidade = next((u for u in resto[i + 1 :]), "")
            break
        registros.append(
            {
                "codigo": codigo,
                "indicador": str(linha[1]).strip(),
                "valor": valor,
                "unidade": unidade,
            }
        )

    proveniencia.registrar_arquivo(
        "SINISA", caminho, f"ano de referência {meta['ano_referencia']}, {meta['municipio']}"
    )
    return pd.DataFrame(registros, columns=["codigo", "indicador", "valor", "unidade"]), meta


def _coordenadas_municipio(sessao) -> tuple[float, float]:
    """
    Latitude e longitude do município pelo geocodificador do Open-Meteo.

    Escolhe o resultado do Brasil cuja divisão de primeiro nível é o Pará.

    Raises:
        ValueError: se nenhum resultado corresponder ao município e à UF.
    """
    resposta = sessao.get(
        config.CLIMA_GEOCODING_API,
        params={"name": config.MUNICIPIO_NOME, "count": 10, "language": "pt"},
        timeout=30,
    )
    resposta.raise_for_status()
    for item in resposta.json().get("results", []):
        if item.get("country_code") == "BR" and item.get("admin1") in {"Pará", "Para"}:
            return float(item["latitude"]), float(item["longitude"])
    raise ValueError(
        f"{config.MUNICIPIO_NOME}/{config.MUNICIPIO_UF} não encontrado no geocodificador"
    )


def carregar_precipitacao(sessao=None) -> pd.DataFrame:
    """
    Precipitação diária no ponto do município, do início ao fim do período.

    Usa a cópia local em config.CLIMA_ARQUIVO se ela cobrir o período;
    senão baixa da API de histórico do Open-Meteo (modelo config.CLIMA_MODELO)
    e grava a cópia, com um arquivo .json ao lado registrando coordenadas,
    modelo e endereço da consulta.

    Args:
        sessao: objeto com método get (requests.Session). Se None, cria um.

    Returns:
        DataFrame com data (datetime) e precipitacao_mm.

    Raises:
        RuntimeError: se o download falhar e não houver cópia local.
    """
    caminho = config.DADOS_BRUTOS / config.CLIMA_ARQUIVO
    meta_caminho = caminho.with_suffix(".json")
    inicio, fim = pd.Timestamp(config.PERIODO_INICIO), pd.Timestamp(config.PERIODO_FIM)

    if caminho.exists():
        local = pd.read_csv(caminho, parse_dates=["data"])
        valida = not local.empty and local["precipitacao_mm"].notna().any()
        meta_local = (
            json.loads(meta_caminho.read_text(encoding="utf-8")) if meta_caminho.exists() else {}
        )
        mesmo_modelo = meta_local.get("modelo") == config.CLIMA_MODELO
        if valida and mesmo_modelo and local["data"].min() <= inicio and local["data"].max() >= fim:
            proveniencia.registrar_arquivo(
                "Precipitação",
                caminho,
                "cópia local",
                origem=config.CLIMA_API,
                baixado_em=meta_local.get("baixado_em"),
            )
            recorte = local[(local["data"] >= inicio) & (local["data"] <= fim)].reset_index(
                drop=True
            )
            recorte.attrs["meta"] = meta_local
            return recorte
        logger.warning("Cópia local de precipitação inválida ou de outro modelo; baixando de novo")

    sessao = sessao or requests.Session()
    try:
        latitude, longitude = config.CLIMA_COORDENADAS or _coordenadas_municipio(sessao)
        parametros = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": str(config.PERIODO_INICIO),
            "end_date": str(config.PERIODO_FIM),
            "daily": "precipitation_sum",
            "timezone": config.CLIMA_FUSO,
            "models": config.CLIMA_MODELO,
        }
        resposta = sessao.get(config.CLIMA_API, params=parametros, timeout=60)
        resposta.raise_for_status()
        corpo = resposta.json()
    except (OSError, ValueError, KeyError) as erro:
        # OSError inclui requests.RequestException (rede e HTTP); ValueError,
        # JSON inválido ou município não encontrado.
        proveniencia.registrar_indisponivel("Precipitação", "Open-Meteo", type(erro).__name__)
        raise RuntimeError(f"Falha ao obter precipitação: {erro}") from erro

    diario = corpo.get("daily", {})
    df = pd.DataFrame(
        {
            "data": pd.to_datetime(diario.get("time", [])),
            "precipitacao_mm": pd.to_numeric(diario.get("precipitation_sum", []), errors="coerce"),
        }
    )

    # Uma série sem nenhum valor não é chuva zero: é ausência de dado.
    if df.empty or df["precipitacao_mm"].isna().all():
        proveniencia.registrar_indisponivel(
            "Precipitação", f"Open-Meteo {config.CLIMA_MODELO}", "série sem valores"
        )
        raise RuntimeError(
            f"O modelo {config.CLIMA_MODELO} não retornou precipitação para o ponto pedido."
        )

    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False)
    meta = proveniencia.registro_download(
        caminho, "Open-Meteo Historical Weather API", config.CLIMA_API, linhas=len(df)
    ) | {
        "modelo": config.CLIMA_MODELO,
        "latitude_pedida": latitude,
        "longitude_pedida": longitude,
        "latitude_grade": corpo.get("latitude"),
        "longitude_grade": corpo.get("longitude"),
        "parametros": parametros,
    }
    meta_caminho.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    proveniencia.registrar_arquivo(
        "Precipitação",
        caminho,
        f"{config.CLIMA_MODELO}, ponto de grade {corpo.get('latitude')}, {corpo.get('longitude')}",
        origem=config.CLIMA_API,
        baixado_em=meta["baixado_em"],
    )
    df.attrs["meta"] = meta
    return df


COLUNAS_SIM = (
    "CAUSABAS",  # causa básica (CID-10)
    "CODMUNRES",  # município de residência
    "DTOBITO",  # data do óbito
    "IDADE",  # idade codificada (unidade + valor)
    "SEXO",
    "RACACOR",
    "LOCOCOR",  # local de ocorrência
)


def carregar_sim(
    uf: str | None = None,
    anos: list[int] | None = None,
) -> pd.DataFrame:
    """
    Carrega os óbitos (SIM, Declaração de Óbito) de residentes do município.

    Os arquivos são anuais por UF. O SIM costuma publicar o ano mais
    recente com atraso; anos sem arquivo ficam registrados como
    indisponíveis, e a lista de anos carregados vai em df.attrs['anos'],
    porque a taxa de mortalidade só pode usar a pessoa-tempo desses anos.

    Fonte: DATASUS, via pysus.ftp.sim (arquivos DO).

    Args:
        uf: sigla da UF. Se None, usa a do config.
        anos: anos a carregar. Se None, usa os do config.

    Returns:
        DataFrame com os óbitos de residentes; attrs['anos'] com os anos lidos.
    """
    uf = uf or config.MUNICIPIO_UF
    anos = anos or config.ANOS

    quadros, anos_lidos = [], []
    for ano in anos:
        rotulo = f"{uf} {ano} DO"
        caminho, leitura = _obter(
            pysus_ftp.sim, "sim", f"DO{uf}{ano}.parquet", rotulo, state=uf, year=ano
        )
        if caminho is None:
            proveniencia.registrar_indisponivel("SIM", rotulo, "sem arquivo DO")
            continue

        try:
            bloco, ausentes = _ler_parquet(caminho, COLUNAS_SIM)
        except ERROS_LEITURA as erro:
            proveniencia.registrar_indisponivel(
                "SIM", rotulo, f"falha de leitura: {type(erro).__name__}"
            )
            continue
        if ausentes:
            logger.warning("%s: colunas ausentes %s", rotulo, sorted(ausentes))

        # CODMUNRES pode vir com 6 ou 7 dígitos; compara os 6 primeiros.
        residentes = bloco[
            bloco["CODMUNRES"].astype(str).str.strip().str[:6] == config.MUNICIPIO_IBGE_6_STR
        ].copy()
        quadros.append(residentes)
        anos_lidos.append(ano)
        _registrar_pysus(
            "SIM",
            "sim",
            caminho,
            f"{rotulo}: {len(bloco)} óbitos na UF, {len(residentes)} de residentes",
            leitura,
            state=uf,
            year=ano,
        )

    if not quadros:
        df = pd.DataFrame(columns=list(COLUNAS_SIM))
    else:
        df = pd.concat(quadros, ignore_index=True)
        unidades = df["IDADE"].astype(str).str.strip().str[0].value_counts().to_dict()
        logger.info("SIM: primeiro dígito de IDADE (unidade) %s", unidades)

    df.attrs["anos"] = anos_lidos
    logger.info("SIM consolidado: %d óbitos de residentes em %s", len(df), anos_lidos)
    return df
