"""
Avaliação da qualidade dos dados.

Nenhum registro é alterado: o que se encontra aqui vai para o relatório,
e o tratamento, quando há, fica em transformacoes.py.

Completitude segue a escala de incompletude de Romero e Cunha (2006):
proporção de campos em branco ou com código de "ignorado".
"""

import re

import pandas as pd

from src import config

PADRAO_CID = re.compile(r"^[A-Z]\d{2}")


def classificar_incompletude(percentual: float) -> str:
    """Classificação de Romero e Cunha para um percentual de incompletude."""
    for limite, rotulo in config.ESCALA_INCOMPLETUDE:
        if limite is None or percentual < limite:
            return rotulo
    return config.ESCALA_INCOMPLETUDE[-1][1]


def _texto(serie: pd.Series) -> pd.Series:
    """Texto limpo; vazio, 'nan' e 'None' viram string vazia."""
    # notna() primeiro: no pandas 3, astype(str) mantém ausentes como NaN
    # em vez de convertê-los para o texto "None".
    texto = serie.astype(str).where(serie.notna(), "").fillna("").str.strip()
    return texto.replace({"nan": "", "None": "", "NaT": "", "<NA>": ""})


def _linha(base: str, campo: str, validos: pd.Series) -> dict:
    total = int(len(validos))
    incompletos = int((~validos).sum())
    percentual = round(incompletos / total * 100, 1) if total else 0.0
    return {
        "base": base,
        "campo": campo,
        "registros": total,
        "incompletos": incompletos,
        "incompletude": percentual,
        "classificacao": classificar_incompletude(percentual) if total else "sem registros",
    }


def _preenchido(df: pd.DataFrame, coluna: str, base: str) -> pd.Series:
    """True quando o campo existe, não está em branco e não é 'ignorado'."""
    if coluna not in df.columns:
        return pd.Series(False, index=df.index)
    texto = _texto(df[coluna])
    ignorados = config.CODIGOS_IGNORADO.get(base, {}).get(coluna, set())
    return (texto != "") & ~texto.isin(ignorados)


def completitude(
    sih: pd.DataFrame, sinan: pd.DataFrame, sim: pd.DataFrame, agua: pd.DataFrame
) -> pd.DataFrame:
    """
    Incompletude dos campos usados nos perfis, por base.

    Args:
        sih: SIH de residentes no período (todas as causas), padronizado.
        sinan: SINAN padronizado e filtrado no período.
        sim: SIM padronizado e filtrado no período.
        agua: SISAGUA de qualidade padronizado e filtrado no período.

    Returns:
        DataFrame com base, campo, registros, incompletos, percentual de
        incompletude e classificação.
    """
    linhas = []

    if not sih.empty:
        linhas += [
            _linha("SIH", "Sexo", _texto(sih["SEXO"]).isin({"1", "2", "3"})),
            _linha("SIH", "Idade", sih["idade_anos"].notna()),
            _linha(
                "SIH",
                "Diagnóstico principal (CID válido)",
                _texto(sih["DIAG_PRINC"]).str.upper().str.match(PADRAO_CID),
            ),
            _linha("SIH", "Data de saída", sih["DT_SAIDA"].notna()),
            _linha("SIH", "Estabelecimento (CNES)", _preenchido(sih, "CNES", "SIH")),
        ]

    if not sinan.empty:
        com_classi = sinan[~sinan["agravo"].isin(config.SINAN_SEM_CLASSI_FIN)]
        linhas += [
            _linha("SINAN", "Sexo", _preenchido(sinan, "CS_SEXO", "SINAN")),
            _linha("SINAN", "Idade", sinan["idade_anos"].notna()),
            _linha("SINAN", "Data dos primeiros sintomas", sinan["DT_SIN_PRI"].notna()),
            _linha("SINAN", "Classificação final*", _preenchido(com_classi, "CLASSI_FIN", "SINAN")),
            _linha("SINAN", "Evolução", _preenchido(sinan, "EVOLUCAO", "SINAN")),
        ]

    if not sim.empty:
        linhas += [
            _linha("SIM", "Sexo", _preenchido(sim, "SEXO", "SIM")),
            _linha("SIM", "Idade", sim["idade_anos"].notna()),
            _linha("SIM", "Raça/cor", _preenchido(sim, "RACACOR", "SIM")),
            _linha(
                "SIM",
                "Causa básica (CID válido)",
                _texto(sim["CAUSABAS"]).str.upper().str.match(PADRAO_CID),
            ),
            _linha("SIM", "Local de ocorrência", _preenchido(sim, "LOCOCOR", "SIM")),
        ]

    if not agua.empty:
        numericos = agua[agua["PARAMETRO"].isin(config.PARAMETROS_NUMERICOS)]
        micro = agua[agua["PARAMETRO"].isin(config.PARAMETROS_MICROBIOLOGICOS)]
        linhas += [
            _linha(
                "SISAGUA",
                "Área de abrangência",
                agua["NO_AREA"].notna()
                if "NO_AREA" in agua.columns
                else pd.Series(False, index=agua.index),
            ),
            _linha(
                "SISAGUA",
                "Solução de abastecimento",
                _preenchido(agua, "NU_SOLUCAO_ABASTECIMENTO", "SISAGUA"),
            ),
            _linha(
                "SISAGUA",
                "Ponto de coleta",
                agua["TP_PONTO_COLETA"].notna()
                if "TP_PONTO_COLETA" in agua.columns
                else pd.Series(False, index=agua.index),
            ),
            _linha(
                "SISAGUA", "Resultado numérico legível", numericos["resultado_numerico"].notna()
            ),
            _linha(
                "SISAGUA",
                "Resultado microbiológico (presente/ausente)",
                micro["resultado_texto"].isin(
                    {config.RESULTADO_PRESENTE, config.RESULTADO_AUSENTE}
                ),
            ),
        ]

    return pd.DataFrame(
        linhas,
        columns=["base", "campo", "registros", "incompletos", "incompletude", "classificacao"],
    )


def consistencia(sih: pd.DataFrame, sinan: pd.DataFrame, agua: pd.DataFrame) -> pd.DataFrame:
    """
    Registros com valores incompatíveis entre si ou fora da faixa possível.

    Nada é removido; a contagem vai para o relatório.

    Returns:
        DataFrame com base, regra, registros avaliados e registros que a violam.
    """
    linhas = []

    def regra(base, descricao, avaliados, violacoes):
        linhas.append(
            {
                "base": base,
                "regra": descricao,
                "avaliados": int(avaliados),
                "inconsistentes": int(violacoes),
            }
        )

    if not sih.empty:
        ambos = sih[sih["DT_INTER"].notna() & sih["DT_SAIDA"].notna()]
        regra(
            "SIH",
            "Data de saída anterior à internação",
            len(ambos),
            (ambos["DT_SAIDA"] < ambos["DT_INTER"]).sum(),
        )
        perm = sih["DIAS_PERM"].dropna()
        regra("SIH", "Dias de permanência negativos", len(perm), (perm < 0).sum())
        regra(
            "SIH",
            "Idade acima de 110 anos",
            sih["idade_anos"].notna().sum(),
            (sih["idade_anos"] > 110).sum(),
        )

    if not sinan.empty:
        ambos = sinan[sinan["DT_NOTIFIC"].notna() & sinan["DT_SIN_PRI"].notna()]
        regra(
            "SINAN",
            "Primeiros sintomas depois da notificação",
            len(ambos),
            (ambos["DT_SIN_PRI"] > ambos["DT_NOTIFIC"]).sum(),
        )

    if not agua.empty:
        num = agua[agua["resultado_numerico"].notna()]
        regra(
            "SISAGUA",
            "Resultado numérico negativo",
            len(num),
            (num["resultado_numerico"] < 0).sum(),
        )
        ph = num[num["PARAMETRO"] == config.PARAMETRO_PH]
        regra(
            "SISAGUA",
            "pH fora de 0 a 14",
            len(ph),
            ((ph["resultado_numerico"] < 0) | (ph["resultado_numerico"] > 14)).sum(),
        )

    return pd.DataFrame(linhas, columns=["base", "regra", "avaliados", "inconsistentes"])


def duplicidade(sih: pd.DataFrame, sinan: pd.DataFrame) -> pd.DataFrame:
    """
    Registros repetidos.

    SIH: mesmo número de AIH. SINAN: sem identificação pessoal nos dados
    públicos, conta como possível duplicidade o mesmo agravo com as mesmas
    datas de notificação e de sintomas, idade e sexo. É uma estimativa;
    nada é removido.

    Returns:
        DataFrame com base, critério, registros e repetidos.
    """
    linhas = []
    if not sih.empty and "N_AIH" in sih.columns:
        linhas.append(
            {
                "base": "SIH",
                "criterio": "Mesmo número de AIH",
                "registros": len(sih),
                "repetidos": int(sih["N_AIH"].duplicated().sum()),
            }
        )
    if not sinan.empty:
        chave = [
            c
            for c in ("agravo", "DT_NOTIFIC", "DT_SIN_PRI", "NU_IDADE_N", "CS_SEXO")
            if c in sinan.columns
        ]
        linhas.append(
            {
                "base": "SINAN",
                "criterio": "Mesmo agravo, datas, idade e sexo (possível)",
                "registros": len(sinan),
                "repetidos": int(sinan.duplicated(subset=chave).sum()),
            }
        )
    return pd.DataFrame(linhas, columns=["base", "criterio", "registros", "repetidos"])
