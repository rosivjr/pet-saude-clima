"""Hepatite A no Sinan (hepatites virais), Brasil, Pará e Parauapebas, 2022–2023."""

import pandas as pd

from src import config

ORIGEM = config.DADOS_BRUTOS / "sinan"  # copiado do cache do PySUS por baixar_sinan.py
COLUNAS = ["HAV", "CLASSI_FIN", "ID_MN_RESI", "DT_DIAG"]


def contar(casos, coluna_ano, ano):
    do_ano = casos[casos[coluna_ano] == ano]
    no_para = int(do_ano["municipio_residencia"].str.startswith(str(config.UF_IBGE)).sum())
    em_pbs = int((do_ano["municipio_residencia"] == config.MUNICIPIO_IBGE_6_STR).sum())
    return len(do_ano), no_para, em_pbs


def main() -> None:
    config.DADOS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    # Carregar os arquivos: o de hepatites é nacional, então só as colunas usadas
    partes = []
    for ano in config.SINAN_HEPATITE_ANOS:
        caminho = ORIGEM / f"HEPABR{ano % 100:02d}.parquet"
        if not caminho.exists():
            raise SystemExit(f"{caminho.name} ausente em data/raw/sinan: rode make baixar-sinan")
        df = pd.read_parquet(caminho, columns=COLUNAS)
        df["ano_arquivo"] = ano
        partes.append(df)
        print(f"{ano}: {len(df)} notificações")
    df = pd.concat(partes, ignore_index=True)

    # Hepatite A confirmada: vírus A e classificação final confirmada (critério no config)
    hav = df["HAV"].astype(str).str.strip() == config.SINAN_HAV_VIRUS_A
    confirmado = df["CLASSI_FIN"].astype(str).str.strip().isin(config.SINAN_HEPATITE_CONFIRMADO)
    hep_a = df[hav & confirmado].copy()
    hep_a["municipio_residencia"] = hep_a["ID_MN_RESI"].astype(str).str[:6]
    hep_a["ano_diag"] = pd.to_datetime(hep_a["DT_DIAG"], errors="coerce").dt.year

    print(f"\nCasos com HAV = 1: {int(hav.sum())} | confirmados: {len(hep_a)}")
    print("Datas de diagnóstico inválidas:", int(hep_a["ano_diag"].isna().sum()))

    # Por ano do arquivo e por ano de diagnóstico, com a referência do Boletim
    linhas = []
    for ano in config.SINAN_HEPATITE_ANOS:
        br_a, pa_a, pbs_a = contar(hep_a, "ano_arquivo", ano)
        br_d, pa_d, pbs_d = contar(hep_a, "ano_diag", ano)
        referencia = config.SINAN_HEPATITE_A_BOLETIM[ano]
        print(f"\n===== {ano} =====")
        print(
            f"Por ano do arquivo:      Brasil {br_a:>5} | Pará {pa_a:>3} | Parauapebas {pbs_a:>2}"
        )
        print(
            f"Por ano de diagnóstico:  Brasil {br_d:>5} | Pará {pa_d:>3} | Parauapebas {pbs_d:>2}"
        )
        print(
            f"Boletim (referência):    Brasil {referencia['Brasil']:>5} | "
            f"Pará {referencia['Pará']:>3}"
        )
        linhas.append(
            {
                "ano": ano,
                "brasil_diag": br_d,
                "para_diag": pa_d,
                "parauapebas_diag": pbs_d,
                "brasil_arquivo": br_a,
                "para_arquivo": pa_a,
                "parauapebas_arquivo": pbs_a,
            }
        )

    pd.DataFrame(linhas).to_csv(config.DADOS_PROCESSADOS / "hepatite_a_sinan.csv", index=False)
    print("\nTabela salva em data/processed/hepatite_a_sinan.csv")


if __name__ == "__main__":
    main()
