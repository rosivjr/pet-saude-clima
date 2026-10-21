"""Cadastro de soluções de abastecimento do SISAGUA e sua ligação com as amostras."""

import logging
from dataclasses import dataclass, field

import pandas as pd

from src import config

from ._comum import _wilson_percentual, ultimo_ano_completo
from .territorio import _positividade

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PerfilAbastecimento:
    """Soluções cadastradas em um ano; desinfecção e filtração são autodeclaradas."""

    total_solucoes: int
    por_tipo: dict[str, int]  # SAA, SAC, SAI
    declaram_desinfeccao: int
    declaram_filtracao: int
    captacao_subterranea: int
    populacao_estimada: float  # soma da população estimada atendida
    ano_referencia: int = 0
    # Percentual de cada tipo no cadastro, sem IC: o cadastro é contagem completa,
    # não amostra (docs/metodos.md).
    percentual_por_tipo: dict[str, float] = field(default_factory=dict)


def composicao_cadastro_por_ano(cadastro: pd.DataFrame) -> pd.DataFrame:
    """
    Composição do cadastro de abastecimento em cada ano.

    Mostra se o cadastro do ano mais recente está completo: uma queda brusca
    no número de soluções pode ser cadastro ainda em atualização, e não
    desativação real.
    """
    colunas = ["ano", "solucoes", "SAA", "SAC", "SAI", "declaram_desinfeccao", "populacao_estimada"]
    if cadastro.empty:
        return pd.DataFrame(columns=colunas)

    linhas = []
    for ano, bloco in cadastro.groupby("ano"):
        tipos = bloco["TP_ABASTECIMENTO"].value_counts()
        linhas.append(
            {
                "ano": int(ano),
                "solucoes": len(bloco),
                "SAA": int(tipos.get("SAA", 0)),
                "SAC": int(tipos.get("SAC", 0)),
                "SAI": int(tipos.get("SAI", 0)),
                "declaram_desinfeccao": int(bloco["DESINFECCAO"].eq(True).sum()),
                "populacao_estimada": float(bloco["NU_VALOR_POPULACAO_ESTIMADA"].sum(skipna=True)),
            }
        )
    return pd.DataFrame(linhas, columns=colunas)


def perfil_abastecimento(
    cadastro: pd.DataFrame,
    ano: int | None = None,
) -> PerfilAbastecimento:
    """
    Caracteriza as soluções cadastradas em um ano.

    Sem ano, usa o último ano completo do período que exista no cadastro,
    porque o cadastro do ano corrente pode estar em atualização. Juntar
    vários anos contaria soluções já desativadas como vigentes.
    """
    if cadastro.empty:
        return PerfilAbastecimento(0, {}, 0, 0, 0, 0.0)

    if ano is None:
        disponiveis = cadastro.loc[cadastro["ano"] <= ultimo_ano_completo(), "ano"]
        ano = int(disponiveis.max()) if not disponiveis.empty else int(cadastro["ano"].max())

    df = cadastro[cadastro["ano"] == ano]
    por_tipo = df["TP_ABASTECIMENTO"].value_counts().to_dict()

    return PerfilAbastecimento(
        total_solucoes=len(df),
        por_tipo=por_tipo,
        declaram_desinfeccao=int(df["DESINFECCAO"].eq(True).sum()),
        declaram_filtracao=int(df["FILTRACAO"].eq(True).sum()),
        captacao_subterranea=int(df["CAPTACAO_SUBTERRANEA"].eq(True).sum()),
        populacao_estimada=float(df["NU_VALOR_POPULACAO_ESTIMADA"].sum(skipna=True)),
        ano_referencia=ano,
        percentual_por_tipo={
            tipo: round(quantidade / len(df) * 100, 1) for tipo, quantidade in por_tipo.items()
        },
    )


def resumo_cloro_areas(cloro_por_area: pd.DataFrame) -> dict[str, int]:
    """Áreas, áreas com base suficiente e quantas destas tiveram 100% abaixo do mínimo de cloro."""
    if cloro_por_area.empty:
        return {"areas": 0, "suficientes": 0, "todas_fora": 0}

    suficientes = cloro_por_area[cloro_por_area["amostra_suficiente"]]
    return {
        "areas": len(cloro_por_area),
        "suficientes": len(suficientes),
        "todas_fora": int((suficientes["fora_do_padrao"] == suficientes["amostras"]).sum()),
    }


def ligar_cadastro_por_ano(
    qualidade: pd.DataFrame,
    cadastro: pd.DataFrame,
    colunas: list[str],
) -> pd.DataFrame:
    """
    Liga cada amostra ao cadastro da sua solução no ano mais próximo.

    Regra: usa o cadastro do mesmo ano ou do ano anterior mais próximo. Se
    não houver, usa o do ano seguinte mais próximo. Amostras sem nenhum
    cadastro da solução ficam sem par. As contagens de cada caso, e o
    número de soluções sem par, ficam em resultado.attrs['ligacao'] e no log.

    O merge_asof só escolhe o ano do cadastro; as colunas vêm de um
    pd.merge com validate="many_to_one", que recusa cadastro repetindo a
    mesma solução no mesmo ano, e indicator=True, que conta as amostras
    sem cadastro.

    As amostras do SISAGUA precisam de 'ano' e NU_SOLUCAO_ABASTECIMENTO, e o
    cadastro padronizado tem uma linha por solução e ano. Devolve as amostras
    com as colunas pedidas do cadastro; as sem par ficam com NaN.

    Raises:
        ValueError: se o cadastro repetir a mesma solução no mesmo ano.
    """
    chave = "NU_SOLUCAO_ABASTECIMENTO"
    amostras = qualidade.dropna(subset=["ano"]).copy()
    amostras[chave] = amostras[chave].astype(str).str.strip()
    amostras["ano"] = amostras["ano"].astype(int)
    amostras["_ordem"] = range(len(amostras))

    cad = cadastro[[chave, "ano", *colunas]].copy()
    cad[chave] = cad[chave].astype(str).str.strip()
    cad["ano"] = cad["ano"].astype(int)
    cad = cad.rename(columns={"ano": "ano_cadastro"})

    # Ano do cadastro de cada amostra: o mesmo ou o anterior; se não houver, o seguinte.
    anos = cad[[chave, "ano_cadastro"]].drop_duplicates()
    anos["ano"] = anos["ano_cadastro"]
    esquerda = amostras[[chave, "ano", "_ordem"]].sort_values("ano")
    direita = anos.sort_values("ano")
    atras = pd.merge_asof(esquerda, direita, on="ano", by=chave, direction="backward")
    frente = pd.merge_asof(esquerda, direita, on="ano", by=chave, direction="forward")
    atras = atras.set_index("_ordem").sort_index()["ano_cadastro"]
    frente = frente.set_index("_ordem").sort_index()["ano_cadastro"]
    amostras["ano_cadastro"] = atras.fillna(frente).to_numpy()

    try:
        resultado = pd.merge(
            amostras,
            cad,
            on=[chave, "ano_cadastro"],
            how="left",
            validate="many_to_one",
            indicator=True,
        )
    except pd.errors.MergeError as erro:
        repetidas = int(cad.duplicated([chave, "ano_cadastro"]).sum())
        raise ValueError(
            f"Cadastro com {repetidas} linha(s) repetindo solução e ano; "
            "a ligação amostra-cadastro ficaria ambígua."
        ) from erro

    sem_cadastro = resultado["_merge"] == "left_only"
    resultado = resultado.drop(columns=["_ordem", "_merge"])
    resultado = resultado[[*amostras.columns.drop("_ordem"), *colunas]]
    diferenca = resultado["ano"] - resultado["ano_cadastro"]
    ligacao = {
        "mesmo_ano": int((diferenca == 0).sum()),
        "ano_anterior": int((diferenca > 0).sum()),
        "ano_seguinte": int((diferenca < 0).sum()),
        "sem_par": int(sem_cadastro.sum()),
        "solucoes_sem_par": int(resultado.loc[sem_cadastro, chave].nunique()),
    }
    resultado.attrs["ligacao"] = ligacao
    logger.info("Ligação amostra-cadastro: %s", ligacao)
    if ligacao["sem_par"]:
        logger.warning(
            "%d amostra(s) de %d solução(ões) sem cadastro em nenhum ano",
            ligacao["sem_par"],
            ligacao["solucoes_sem_par"],
        )
    return resultado


def divergencia_desinfeccao(
    cadastro: pd.DataFrame,
    qualidade: pd.DataFrame,
) -> dict[str, float | int]:
    """
    Compara a desinfecção declarada no cadastro com o cloro medido.

    Cada amostra é ligada ao cadastro da solução no ano mais próximo
    (ligar_cadastro_por_ano); as contagens da ligação vêm na chave 'ligacao'.
    O campo DESINFECCAO é autodeclarado.
    """
    if cadastro.empty or qualidade.empty:
        logger.warning("Dados insuficientes para avaliar divergência")
        return {}

    cloro = qualidade[
        (qualidade["PARAMETRO"] == config.PARAMETRO_CLORO) & qualidade["resultado_numerico"].notna()
    ]
    ligada = ligar_cadastro_por_ano(cloro, cadastro, ["DESINFECCAO"])
    declarantes = ligada[ligada["DESINFECCAO"] == True]  # noqa: E712

    if declarantes.empty:
        return {
            "solucoes_declarantes": 0,
            "amostras_avaliadas": 0,
            "percentual_fora": 0.0,
            "ligacao": ligada.attrs["ligacao"],
        }

    fora = int((declarantes["resultado_numerico"] < config.CLORO_RESIDUAL_MINIMO).sum())
    total = len(declarantes)
    inferior, superior = _wilson_percentual(fora, total)

    return {
        "solucoes_declarantes": int(declarantes["NU_SOLUCAO_ABASTECIMENTO"].nunique()),
        "amostras_avaliadas": total,
        "fora_do_padrao": fora,
        "percentual_fora": round(fora / total * 100, 1),
        "ic_inferior": inferior,
        "ic_superior": superior,
        "ligacao": ligada.attrs["ligacao"],
    }


def ecoli_por_captacao(
    qualidade: pd.DataFrame,
    cadastro: pd.DataFrame,
) -> pd.DataFrame:
    """
    Relaciona a origem da água com a presença de Escherichia coli.

    Cada amostra é ligada ao cadastro da solução no ano mais próximo. O
    cadastro registra só se a captação é subterrânea, sem distinguir
    profundidade. Amostras da mesma solução não são independentes: o IC de
    Wilson aqui é descritivo e subestima a incerteza. As contagens da
    ligação ficam em resultado.attrs['ligacao'].
    """
    colunas = [
        "origem",
        "amostras",
        "positivos",
        "percentual_positivo",
        "ic_inferior",
        "ic_superior",
    ]
    chave = "NU_SOLUCAO_ABASTECIMENTO"

    if chave not in qualidade.columns or cadastro.empty:
        logger.warning("Chave de ligação ausente; cruzamento não realizado")
        return pd.DataFrame(columns=colunas)

    micro = qualidade[qualidade["PARAMETRO"] == config.PARAMETRO_E_COLI]
    if micro.empty:
        logger.warning("Sem amostras de E. coli para cruzar com a captação")
        return pd.DataFrame(columns=colunas)

    ligada = ligar_cadastro_por_ano(
        micro, cadastro, ["CAPTACAO_SUBTERRANEA", "CAPTACAO_SUPERFICIAL"]
    )
    ligacao = ligada.attrs["ligacao"]
    ligada = ligada[ligada["ano_cadastro"].notna()]

    if ligada.empty:
        logger.warning("Nenhuma amostra casou com o cadastro de soluções")
        return pd.DataFrame(columns=colunas)

    sub = ligada["CAPTACAO_SUBTERRANEA"].eq(True)
    sup = ligada["CAPTACAO_SUPERFICIAL"].eq(True)
    ligada["origem"] = "Não informada"
    ligada.loc[sub & ~sup, "origem"] = "Subterrânea"
    ligada.loc[sup & ~sub, "origem"] = "Superficial"
    ligada.loc[sub & sup, "origem"] = "Mista (subterrânea e superficial)"

    resumo = _positividade(ligada, "origem", "origem")
    resumo = resumo.sort_values("percentual_positivo", ascending=False).reset_index(drop=True)
    resumo.attrs["ligacao"] = ligacao
    return resumo
