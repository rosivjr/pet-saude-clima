"""Compara o resultado do Brasil com diferentes regras de correção das unidades."""

from dda import comum
from dda.limpeza_dda import COLUNAS_UNIDADES, corrigir_unidades
from src import config


def main() -> None:
    for ano in config.DDA_ANOS:
        bruto = comum.ler_ano(ano)
        casos = bruto[config.DDA_FAIXAS].sum().sum()
        print(f"\n===== Brasil, {ano} =====")
        print(f"sem correção       | casos/unid-sem {casos / bruto['nu_unidades_inf'].sum():.2f}")

        for limite in (10, 50, 100, 1000):
            df = corrigir_unidades(bruto, limite=limite, mostrar=False)
            corrigidos = " | ".join(
                f"corrigidos {coluna} {(df[coluna] != bruto[coluna]).sum():>4}"
                for coluna in COLUNAS_UNIDADES
            )
            razao = casos / df["nu_unidades_inf"].sum()
            completude = 100 * df["nu_unidades_inf"].sum() / df["nu_usaude_sem"].sum()
            print(
                f"limite {limite:>4}×        | casos/unid-sem {razao:.2f} | "
                f"{corrigidos} | completude {completude:.1f}%"
            )


if __name__ == "__main__":
    main()
