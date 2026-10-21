"""
Padronização e filtros das tabelas carregadas, sem calcular indicadores.

Padroniza SIH, SINAN, SIM, SISAGUA, cadastro de abastecimento e CNES
(tipos, idade em anos, grupo de agravo pelo CID de 3 caracteres,
classificação final do SINAN, resultado do SISAGUA em número e texto) e
aplica os recortes de período, ano, município, tipo de AIH e agravo. Cada
filtro anota na proveniência as linhas que entraram e saíram.
"""

import logging

import numpy as np
import pandas as pd

from src import config, proveniencia

logger = logging.getLogger(__name__)


def converter_decimal_brasileiro(serie: pd.Series) -> pd.Series:
    """
    Converte uma série de texto com vírgula decimal para número.

    Valores que não representam número (ex.: 'PRESENTE', 'AUSENTE') viram NaN
    em vez de causar erro, permitindo que colunas mistas sejam processadas.

    O ponto só é aceito como separador de milhar seguido de vírgula decimal
    (config.PADRAO_MILHAR_BRASILEIRO). Qualquer outro ponto ('0.5', '1.234')
    é ambíguo e interrompe a conversão, pois lido como milhar mudaria o
    valor (decisão 0010).

    Args:
        serie: série de texto no formato brasileiro ('1.234,56').

    Raises:
        ValueError: se algum valor tiver ponto fora do padrão de milhar.
    """
    texto = serie.astype(str).str.strip()

    com_ponto = texto.str.contains(".", regex=False)
    ambiguos = int((com_ponto & ~texto.str.fullmatch(config.PADRAO_MILHAR_BRASILEIRO)).sum())
    if ambiguos:
        raise ValueError(
            f"{ambiguos} {'valor' if ambiguos == 1 else 'valores'} com ponto fora do "
            "padrão de milhar brasileiro (ex.: 1.234,56); confira o formato da fonte"
        )

    texto = texto.str.replace(".", "", regex=False)  # separador de milhar
    texto = texto.str.replace(",", ".", regex=False)  # separador decimal
    return pd.to_numeric(texto, errors="coerce")


def _normalizar_texto(serie: pd.Series) -> pd.Series:
    """
    Padroniza campos de texto livre para permitir agrupamento confiável.

    Bases do DATASUS trazem a mesma área escrita de formas diferentes
    ('Rio Verde', 'RIO VERDE', ' rio verde '). Sem padronizar, cada grafia
    seria tratada como categoria distinta.

    Returns:
        Série em caixa alta, sem espaços nas bordas, com vazios como None.
    """
    return serie.astype(str).str.strip().str.upper().replace({"NAN": None, "NONE": None, "": None})


def registrar_etapa(
    etapa: str,
    motivo: str,
    antes: int,
    depois: int,
    tipo: str = "descarte",
) -> int:
    """
    Registra na proveniência e no log as linhas que entraram e saíram de um filtro.

    Anota inclusive filtros que não removeram nada, para que a tabela de
    etapas do relatório mostre todo o caminho dos dados. É o único log do
    filtro: em WARNING quando um descarte remove linhas, em INFO nos demais.

    Args:
        etapa: fonte e filtro (ex.: 'SIH: período').
        motivo: o que o filtro removeu.
        tipo: 'descarte' (dado inválido ou fora da regra) ou 'recorte'
              (fora do escopo do estudo, sem perda de dado).

    Returns:
        Número de linhas removidas.

    Raises:
        ValueError: se depois for negativo ou maior que antes, ou o tipo for outro.
    """
    if tipo not in ("descarte", "recorte"):
        raise ValueError(f"Tipo de etapa desconhecido: {tipo}")
    if not 0 <= depois <= antes:
        raise ValueError(f"{etapa}: {depois} linhas depois de {antes} antes do filtro")
    removidas = int(antes) - int(depois)
    nivel = logging.WARNING if tipo == "descarte" and removidas else logging.INFO
    logger.log(
        nivel, "%s: %d de %d linhas removidas (%s, %s)", etapa, removidas, antes, tipo, motivo
    )
    proveniencia.registrar_etapa(etapa, tipo, motivo, antes, depois)
    return removidas


def _faixa_etaria(idade_anos: pd.Series) -> pd.Series:
    """Classifica idades em anos nas faixas do config (primeira faixa: <1)."""
    return pd.cut(
        idade_anos,
        bins=list(config.FAIXA_ETARIA_LIMITES),
        labels=list(config.FAIXA_ETARIA_ROTULOS),
        right=True,
    )


def filtrar_periodo(
    df: pd.DataFrame,
    coluna_data: str,
    fonte: str = "",
) -> pd.DataFrame:
    """
    Mantém apenas os registros entre config.PERIODO_INICIO e PERIODO_FIM.

    O recorte é feito pela data do evento (internação, notificação, coleta),
    não pelo ano do arquivo. Registros com data inválida e registros fora
    do período são contados separadamente e anotados na proveniência, com
    o nome do sistema dado em fonte. A coluna de data já deve estar
    convertida.
    """
    inicio = pd.Timestamp(config.PERIODO_INICIO)
    fim = pd.Timestamp(config.PERIODO_FIM)

    sem_data = df[coluna_data].isna()
    dentro = df[coluna_data].between(inicio, fim)
    fora = ~sem_data & ~dentro

    n_sem_data, n_fora = int(sem_data.sum()), int(fora.sum())
    registrar_etapa(f"{fonte}: período", f"{coluna_data} inválida", len(df), len(df) - n_sem_data)
    registrar_etapa(
        f"{fonte}: período",
        f"{coluna_data} fora do período",
        len(df) - n_sem_data,
        len(df) - n_sem_data - n_fora,
        tipo="recorte",
    )
    return df[dentro]


def filtrar_anos(df: pd.DataFrame, coluna_ano: str = "ano", fonte: str = "") -> pd.DataFrame:
    """
    Mantém apenas os registros dos anos definidos em config.ANOS.

    Usada onde só existe o ano (cadastro de abastecimento). Para eventos com
    data, prefira filtrar_periodo. A etapa fica na proveniência com o nome
    do sistema dado em fonte.
    """
    antes = len(df)
    df = df[df[coluna_ano].isin(config.ANOS)]
    registrar_etapa(
        f"{fonte}: ano",
        f"{coluna_ano} fora de {config.ANOS[0]} a {config.ANOS[-1]}",
        antes,
        len(df),
        tipo="recorte",
    )
    return df


def padronizar_sisagua(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame bruto do SISAGUA.

    Converte a data de coleta, separa os resultados numéricos dos
    qualitativos, normaliza os campos territoriais e adiciona colunas
    derivadas de tempo. Recebe a saída de carregadores.carregar_sisagua() e
    devolve uma cópia; o original não é modificado.
    """
    df = df.copy()

    df["DT_COLETA"] = pd.to_datetime(df["DT_COLETA"], errors="coerce")

    sem_data = df["DT_COLETA"].isna().sum()
    if sem_data:
        logger.warning("%d registros com data de coleta inválida", sem_data)

    df["ano"] = df["DT_COLETA"].dt.year
    df["mes"] = df["DT_COLETA"].dt.month

    df["resultado_numerico"] = converter_decimal_brasileiro(df["RESULTADO"])
    df["resultado_texto"] = df["RESULTADO"].astype(str).str.strip().str.upper()

    df["tipo_parametro"] = "outro"
    df.loc[df["PARAMETRO"].isin(config.PARAMETROS_NUMERICOS), "tipo_parametro"] = "numerico"
    df.loc[df["PARAMETRO"].isin(config.PARAMETROS_MICROBIOLOGICOS), "tipo_parametro"] = (
        "microbiologico"
    )

    for coluna in ("NO_AREA", "NO_CATEGORIA_AREA", "TP_PONTO_COLETA", "TP_LOCAL", "NO_LOCAL"):
        if coluna in df.columns:
            df[coluna] = _normalizar_texto(df[coluna])

    if "NO_AREA" in df.columns:
        sem_area = df["NO_AREA"].isna().sum()
        if sem_area:
            logger.warning("%d registros sem área de abrangência identificada", sem_area)

    logger.info(
        "SISAGUA padronizado: %d registros (%s)",
        len(df),
        df["tipo_parametro"].value_counts().to_dict(),
    )
    return df


def _classificar_grupo_agravo(cid: str) -> str | None:
    """
    Identifica a qual grupo de agravo um código CID-10 pertence.

    A comparação usa os 3 primeiros caracteres, pois o SIH grava o CID
    sem ponto e com o 4º dígito (ex.: 'A090' para A09.0). Devolve None se
    o código não pertencer a nenhum grupo.
    """
    if not isinstance(cid, str) or len(cid) < 3:
        return None

    prefixo = cid[:3].upper()

    for grupo, codigos in config.GRUPOS_AGRAVO.items():
        if prefixo in codigos:
            return grupo

    return None


def idade_sih_em_anos(idade: pd.Series, cod_idade: pd.Series) -> pd.Series:
    """
    Converte a idade do SIH para anos completos.

    A unidade vem da coluna COD_IDADE. Dias e meses viram 0 (menor de 1
    ano), o código de 100 anos ou mais soma 100 ao valor e códigos
    desconhecidos viram NaN.
    """
    valor = pd.to_numeric(idade, errors="coerce")
    codigo = cod_idade.astype(str).str.strip()

    return pd.Series(
        np.select(
            [
                codigo.isin([config.SIH_COD_IDADE_DIAS, config.SIH_COD_IDADE_MESES]),
                codigo == config.SIH_COD_IDADE_ANOS,
                codigo == config.SIH_COD_IDADE_CEM_MAIS,
            ],
            [0, valor, valor + 100],
            default=np.nan,
        ),
        index=idade.index,
        dtype="float",
    )


def filtrar_aih_normal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mantém apenas AIH tipo 1 (normal).

    AIH tipo 5 (longa permanência) é continuação de uma internação e
    duplicaria a contagem (Bittencourt, Camacho e Leal, Cad Saúde Pública 2006,
    p. 26; decisão 0009).
    No diagnóstico de 2023-2026, todas as AIH eram tipo 1; o filtro fica
    como proteção para competências futuras.
    """
    antes = len(df)
    df = df[df["IDENT"].astype(str).str.strip() == config.SIH_IDENT_NORMAL]
    registrar_etapa("SIH: tipo de AIH", "AIH diferente do tipo 1", antes, len(df))
    return df


def padronizar_sih(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame bruto do SIH (AIH Reduzida).

    Converte datas, normaliza idade e sexo, e classifica cada internação
    no grupo de agravo correspondente. Recebe a saída de
    carregadores.carregar_sih() e devolve uma cópia; o original não é
    modificado.
    """
    df = df.copy()

    for coluna in ("DT_INTER", "DT_SAIDA"):
        df[coluna] = pd.to_datetime(df[coluna].astype(str), format="%Y%m%d", errors="coerce")

    sem_data = df["DT_INTER"].isna().sum()
    if sem_data:
        logger.warning("%d internações com data de internação inválida", sem_data)

    df["ano"] = df["DT_INTER"].dt.year
    df["mes"] = df["DT_INTER"].dt.month

    df["idade_anos"] = idade_sih_em_anos(df["IDADE"], df["COD_IDADE"])
    df["faixa_etaria"] = _faixa_etaria(df["idade_anos"])

    # SEXO: 1 = masculino; 3 = feminino (2 aparece em registros antigos).
    df["sexo"] = (
        df["SEXO"]
        .astype(str)
        .str.strip()
        .map({"1": config.SEXO_MASCULINO, "2": config.SEXO_FEMININO, "3": config.SEXO_FEMININO})
    )

    df["grupo_agravo"] = df["DIAG_PRINC"].apply(_classificar_grupo_agravo)

    df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
    df["DIAS_PERM"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce")

    logger.info("SIH padronizado: %d internações", len(df))
    return df


def filtrar_municipio_sih(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mantém as internações de residentes no município (config.MUNICIPIO_IBGE_6_STR).

    Aceita o SIH bruto ou padronizado.
    """
    antes = len(df)
    residentes = df["MUNIC_RES"].astype(str).str.strip() == config.MUNICIPIO_IBGE_6_STR
    df = df[residentes]
    registrar_etapa(
        "SIH: município", "residência em outro município", antes, len(df), tipo="recorte"
    )
    return df


def filtrar_agravos(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém apenas internações classificadas em algum grupo de agravo."""
    antes = len(df)
    df = df[df["grupo_agravo"].notna()]
    registrar_etapa(
        "SIH: grupo de agravo", "CID fora dos grupos de agravo", antes, len(df), tipo="recorte"
    )

    logger.info(
        "Agravos selecionados: %d internações em %d grupos",
        len(df),
        df["grupo_agravo"].nunique(),
    )
    return df


def filtrar_drsai(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mantém apenas internações dos grupos do indicador DRSAI (config.GRUPOS_DRSAI).

    Saem as arboviroses fora da lista da FUNASA, o grupo de sensibilidade e o
    contexto climático, que o relatório mostra à parte.
    """
    antes = len(df)
    df = df[df["grupo_agravo"].isin(config.GRUPOS_DRSAI)]
    registrar_etapa(
        "SIH: DRSAI",
        "grupo fora do DRSAI (outras arboviroses, sensibilidade, clima)",
        antes,
        len(df),
        tipo="recorte",
    )
    return df


def idade_sinan_em_anos(nu_idade_n: pd.Series) -> pd.Series:
    """
    Decodifica NU_IDADE_N do SINAN para anos completos.

    O primeiro dígito é a unidade (1 hora, 2 dia, 3 mês, 4 ano) e os
    demais, o valor. Horas, dias e meses viram 0 (menor de 1 ano).
    """
    texto = nu_idade_n.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    unidade = texto.str[0]
    valor = pd.to_numeric(texto.str[1:], errors="coerce")

    return pd.Series(
        np.select(
            [
                unidade.isin(config.SINAN_UNIDADES_MENOR_1_ANO),
                unidade == config.SINAN_UNIDADE_ANOS,
            ],
            [0, valor],
            default=np.nan,
        ),
        index=nu_idade_n.index,
        dtype="float",
    )


def _codigo_classi(valor) -> str | None:
    """CLASSI_FIN como texto ('1', '13'); o float 1.0 vira '1'; vazio vira None."""
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    if texto.endswith(".0") and texto[:-2].isdigit():
        texto = texto[:-2]
    return texto or None


def classificar_sinan(agravo: pd.Series, classi_fin: pd.Series) -> pd.Series:
    """
    Rótulo da classificação final de cada notificação (decisão 0001).

    Os códigos de CLASSI_FIN variam entre fichas e vêm de
    config.SINAN_CLASSI_FIN. Agravos de config.SINAN_SEM_CLASSI_FIN recebem
    config.SINAN_FICHA_SEM_CLASSI; campo vazio, SINAN_SEM_CLASSIFICACAO;
    código fora da lista, SINAN_OUTRO_CODIGO.

    Args:
        agravo: nome do agravo (coluna 'agravo' do carregador).
        classi_fin: coluna CLASSI_FIN bruta.

    Returns:
        Série de rótulos, com o mesmo índice.
    """
    sigla_por_nome = {nome: sigla for sigla, (nome, _) in config.SINAN_AGRAVOS.items()}
    rotulos = []
    for nome, valor in zip(agravo, classi_fin, strict=True):
        if nome in config.SINAN_SEM_CLASSI_FIN:
            rotulos.append(config.SINAN_FICHA_SEM_CLASSI)
            continue
        codigo = _codigo_classi(valor)
        if codigo is None:
            rotulos.append(config.SINAN_SEM_CLASSIFICACAO)
            continue
        codigos = config.SINAN_CLASSI_FIN.get(sigla_por_nome.get(nome), {})
        rotulos.append(codigos.get(codigo, config.SINAN_OUTRO_CODIGO))
    return pd.Series(rotulos, index=agravo.index, dtype=object)


def padronizar_sinan(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame bruto do SINAN.

    Converte datas, decodifica a idade, extrai colunas temporais e rotula a
    classificação final (coluna 'classificacao', ver classificar_sinan).
    A classificação em grupo de agravo já vem preenchida pelo carregador.
    Recebe a saída de carregadores.carregar_sinan() e devolve uma cópia; o
    original não é modificado.
    """
    df = df.copy()

    if df.empty:
        logger.warning("SINAN sem registros para padronizar")
        return df

    df["DT_NOTIFIC"] = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce")
    df["DT_SIN_PRI"] = pd.to_datetime(df["DT_SIN_PRI"], errors="coerce")

    sem_data = df["DT_NOTIFIC"].isna().sum()
    if sem_data:
        logger.warning("%d notificações com data inválida", sem_data)

    df["ano"] = df["DT_NOTIFIC"].dt.year
    df["mes"] = df["DT_NOTIFIC"].dt.month

    df["idade_anos"] = idade_sinan_em_anos(df["NU_IDADE_N"])
    df["faixa_etaria"] = _faixa_etaria(df["idade_anos"])

    df["sexo"] = (
        df["CS_SEXO"]
        .astype(str)
        .str.strip()
        .str.upper()
        .map({"M": config.SEXO_MASCULINO, "F": config.SEXO_FEMININO})
    )

    if "agravo" in df.columns:
        classi = df["CLASSI_FIN"] if "CLASSI_FIN" in df.columns else pd.Series(pd.NA, df.index)
        df["classificacao"] = classificar_sinan(df["agravo"], classi)
        outros = int((df["classificacao"] == config.SINAN_OUTRO_CODIGO).sum())
        if outros:
            logger.warning("%d notificações com CLASSI_FIN fora dos códigos conferidos", outros)

    logger.info("SINAN padronizado: %d notificações", len(df))
    return df


def idade_sim_em_anos(idade: pd.Series) -> pd.Series:
    """
    Decodifica a IDADE do SIM para anos completos.

    Primeiro dígito: unidade (0 minutos, 1 horas, 2 dias, 3 meses, 4 anos,
    5 = 100 anos ou mais). Minutos, horas, dias e meses viram 0; o código
    5 soma 100 ao valor. "000" (idade ignorada) e códigos desconhecidos
    viram NaN.
    """
    texto = idade.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    unidade = texto.str[0]
    valor = pd.to_numeric(texto.str[1:], errors="coerce")
    return pd.Series(
        np.select(
            [
                texto == config.SIM_IDADE_IGNORADA,
                unidade.isin(config.SIM_UNIDADES_MENOR_1_ANO),
                unidade == config.SIM_UNIDADE_ANOS,
                unidade == config.SIM_UNIDADE_CEM_MAIS,
            ],
            [np.nan, 0, valor, valor + 100],
            default=np.nan,
        ),
        index=idade.index,
        dtype="float",
    )


def padronizar_sim(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza os óbitos do SIM.

    Converte a data do óbito (DDMMAAAA), decodifica a idade, classifica a
    causa básica nos grupos de agravo e mantém os anos lidos em attrs.
    Recebe a saída de carregadores.carregar_sim().
    """
    anos = df.attrs.get("anos", [])
    df = df.copy()
    if df.empty:
        df.attrs["anos"] = anos
        return df

    texto = df["DTOBITO"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(8)
    df["DTOBITO"] = pd.to_datetime(texto, format="%d%m%Y", errors="coerce")
    df["ano"] = df["DTOBITO"].dt.year
    df["mes"] = df["DTOBITO"].dt.month

    df["idade_anos"] = idade_sim_em_anos(df["IDADE"])
    df["faixa_etaria"] = _faixa_etaria(df["idade_anos"])
    df["sexo"] = (
        df["SEXO"]
        .astype(str)
        .str.strip()
        .map({"1": config.SEXO_MASCULINO, "2": config.SEXO_FEMININO})
    )
    df["grupo_agravo"] = (
        df["CAUSABAS"].astype(str).str.strip().str.upper().apply(_classificar_grupo_agravo)
    )

    df.attrs["anos"] = anos
    logger.info("SIM padronizado: %d óbitos", len(df))
    return df


def padronizar_populacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o cadastro de soluções de abastecimento e população atendida.

    Mantém uma linha por solução e por ano (a última de cada ano), para que
    a amostra de 2023 seja ligada ao cadastro vigente em 2023, e não ao
    cadastro mais recente. Recebe a saída de
    carregadores.carregar_populacao_abastecida() e devolve uma cópia.
    """
    df = df.copy()

    if df.empty:
        logger.warning("Cadastro de população sem registros")
        return df

    for coluna in (
        "CAPTACAO_SUPERFICIAL",
        "CAPTACAO_SUBTERRANEA",
        "CAPTACAO_AGUA_CHUVA",
        "FILTRACAO",
        "DESINFECCAO",
    ):
        if coluna in df.columns:
            df[coluna] = (
                df[coluna]
                .astype(str)
                .str.strip()
                .str.upper()
                .map({"SIM": True, "NÃO": False, "NAO": False})
            )

    for coluna in ("NU_VALOR_POPULACAO_ESTIMADA", "NU_VALOR_RURAL", "NU_VALOR_URBANA"):
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df["ano"] = pd.to_numeric(df["NU_ANO"], errors="coerce")
    df["NU_SOLUCAO_ABASTECIMENTO"] = df["NU_SOLUCAO_ABASTECIMENTO"].astype(str).str.strip()
    df = filtrar_anos(df, fonte="SISAGUA cadastro")

    antes = len(df)
    df = (
        df.drop_duplicates(["NU_SOLUCAO_ABASTECIMENTO", "ano"], keep="last")
        .sort_values(["NU_SOLUCAO_ABASTECIMENTO", "ano"])
        .reset_index(drop=True)
    )
    registrar_etapa(
        "SISAGUA cadastro: dedup", "deduplicação: última linha por solução e ano", antes, len(df)
    )

    logger.info(
        "Cadastro padronizado: %d registros de %d soluções",
        len(df),
        df["NU_SOLUCAO_ABASTECIMENTO"].nunique(),
    )
    return df


def padronizar_cnes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o cadastro de estabelecimentos do CNES.

    Recebe a saída de carregadores.carregar_cnes() e devolve uma cópia; o
    original não é modificado.
    """
    df = df.copy()

    if df.empty:
        logger.warning("CNES sem registros para padronizar")
        return df

    for coluna in ("CNES", "CODUFMUN", "TP_UNID"):
        if coluna in df.columns:
            df[coluna] = df[coluna].astype(str).str.strip()

    for coluna in ("VINC_SUS", "LEITHOSP", "URGEMERG"):
        if coluna in df.columns:
            df[coluna] = df[coluna].astype(str).str.strip() == "1"

    df["tipo_unidade"] = df["TP_UNID"].map(config.CNES_TIPOS_UNIDADE)

    nao_mapeados = df["tipo_unidade"].isna().sum()
    if nao_mapeados:
        codigos = sorted(df.loc[df["tipo_unidade"].isna(), "TP_UNID"].unique())
        logger.info(
            "%d estabelecimentos com tipo não mapeado: %s",
            nao_mapeados,
            codigos,
        )
        df["tipo_unidade"] = df["tipo_unidade"].fillna("Tipo " + df["TP_UNID"].astype(str))

    logger.info("CNES padronizado: %d estabelecimentos", len(df))
    return df


def filtrar_municipio_cnes(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém só os estabelecimentos do município (config.MUNICIPIO_IBGE_6_STR)."""
    antes = len(df)
    df = df[df["CODUFMUN"] == config.MUNICIPIO_IBGE_6_STR]
    registrar_etapa(
        "CNES: município", "estabelecimento em outro município", antes, len(df), tipo="recorte"
    )
    return df
