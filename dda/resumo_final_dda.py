"""Resumo final da DDA (Sivep-DDA) com correção das unidades, nos anos de config.DDA_ANOS."""

from dda import comum
from dda.limpeza_dda import corrigir_unidades
from src import config


def resumo(recorte, nome):
    casos = recorte[config.DDA_FAIXAS].sum().sum()
    informantes = recorte["nu_unidades_inf"].sum()
    implantadas = recorte["nu_usaude_sem"].sum()
    menores5 = recorte[["nu_m1ano", "nu_1a4"]].sum().sum()
    print(
        f"{nome:12s} | casos {int(casos):>9} | <5 anos {100 * menores5 / casos:5.1f}% | "
        f"casos/unid-sem {casos / informantes:5.2f} | "
        f"completude {100 * informantes / implantadas:5.1f}%"
    )


def main() -> None:
    for ano in config.DDA_ANOS:
        df = comum.ler_ano(ano)
        print(f"\n==================== {ano} ====================")
        df = corrigir_unidades(df)

        se_max = config.DDA_SE_MAX
        periodos = {
            "ano completo": df,
            f"SE 1 a {se_max}": df[df["sem_epid_week"] <= se_max],
        }
        for rotulo, periodo in periodos.items():
            print(f"\n--- {rotulo} ---")
            resumo(periodo[periodo["municipio_ibge"] == config.MUNICIPIO_IBGE_6], "Parauapebas")
            resumo(periodo[periodo["uf_ibge"] == config.UF_IBGE], "Pará")
            resumo(periodo, "Brasil")


if __name__ == "__main__":
    main()
