"""
Internações SIH-RD, Brasil, nas competências de config.SIH_COMPETENCIAS_NACIONAIS:
contagens agregadas lidas do disco.
"""

import pandas as pd

from sih import comum
from src import config
from src.transformacoes import filtrar_aih_normal

COLUNAS = ["MUNIC_RES", "DIAG_PRINC", "DT_INTER", "IDENT"]


def classificar(cid3: pd.Series) -> pd.Series:
    grupo = pd.Series("outras", index=cid3.index)
    cids = config.CID_RELATORIO_DDA
    grupo[cid3.isin(cids["diarreia"])] = "diarreia_A00_A09"
    grupo[cid3.isin(cids["hepatite_a"])] = "hepatite_a_B15"
    grupo[cid3.isin(cids["desidratacao"])] = "desidratacao_E86"
    grupo[cid3.isin(cids["gastro_nao_infecciosa"])] = "gastro_nao_infecciosa_K52"
    return grupo


def resumo(tabela: pd.DataFrame, filtro_mes: pd.Series, rotulo: str) -> None:
    por_grupo = (
        tabela[filtro_mes].groupby(["ano", "grupo"])[["brasil", "para", "parauapebas"]].sum()
    )
    todas = por_grupo.groupby("ano").sum()
    print(f"\n===== {rotulo} =====")
    print(por_grupo.to_string())
    print("\nTodas as internações:")
    print(todas.to_string())
    print("\nProporção de diarreia (A00–A09) entre todas as internações (%):")
    diarreia = por_grupo.xs("diarreia_A00_A09", level="grupo")
    print((100 * diarreia / todas).round(2).to_string())


def main() -> None:
    config.DADOS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    # Competências de processamento de todas as UFs
    esperados = [
        config.PYSUS_PASTA_SIH / comum.nome_rd(uf, ano, mes)
        for uf in config.UFS
        for ano, meses in config.SIH_COMPETENCIAS_NACIONAIS.items()
        for mes in meses
    ]
    faltando = [p.name for p in esperados if not p.exists()]
    print(f"Arquivos esperados: {len(esperados)} | no disco: {len(esperados) - len(faltando)}")
    faltando_pa = [n for n in faltando if n.startswith("RDPA")]
    print(f"Arquivos do Pará faltando: {faltando_pa or 'nenhum'}")

    partes = []
    for arquivo in (p for p in esperados if p.exists()):
        # Só AIH do tipo 1, para não contar continuações (decisão 0009)
        df = comum.filtrar_anos_dda(filtrar_aih_normal(comum.ler_rd(arquivo, COLUNAS)))
        df["grupo"] = classificar(df["cid3"])
        df["para_res"] = df["MUNIC_RES"].str.startswith(str(config.UF_IBGE))
        df["pbs_res"] = df["MUNIC_RES"] == config.MUNICIPIO_IBGE_6_STR
        partes.append(
            df.groupby(["ano", "mes", "grupo"])
            .agg(
                brasil=("grupo", "size"),
                para=("para_res", "sum"),
                parauapebas=("pbs_res", "sum"),
            )
            .reset_index()
        )

    tabela = pd.concat(partes).groupby(["ano", "mes", "grupo"], as_index=False).sum()
    tabela.to_csv(config.DADOS_PROCESSADOS / "sih_agregado_brasil.csv", index=False)

    ultimo_ano = max(config.DDA_ANOS)
    meses = config.SIH_MESES_COMPARACAO
    resumo(tabela, tabela["mes"].between(1, 12), f"Ano completo ({ultimo_ano} incompleto)")
    resumo(tabela, tabela["mes"].isin(meses), comum.rotulo_meses(meses))
    print("\nObservação: colunas 'brasil' incompletas enquanto faltarem arquivos de outras UFs.")
    print("Tabela salva em data/processed/sih_agregado_brasil.csv")


if __name__ == "__main__":
    main()
