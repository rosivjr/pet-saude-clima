from pathlib import Path

import pandas as pd

raw = Path("../data/raw")
COD_PBS = 150553
FAIXAS = ["nu_m1ano", "nu_1a4", "nu_5a9", "nu_10oumais", "nu_faixign"]
PLANOS = ["nu_planoa", "nu_planob", "nu_planoc", "nu_planoign"]

cb = pd.read_csv(raw / "metadata" / "sivep_dda_codebook.csv")
alvo = PLANOS + ["nu_usaude_sem", "nu_unidades_inf", "lo_surto", "lo_alteracao"]
print(cb[cb["clean_name"].isin(alvo)][["clean_name", "description", "notes"]].to_string())


def resumo(sub, nome):
    casos = sub[FAIXAS].sum().sum()
    unid_sem = sub["nu_unidades_inf"].sum()
    print(f"\n--- {nome} ---")
    print("Casos:", int(casos))
    print("Menores de 5 anos (%):", round(100 * sub[["nu_m1ano", "nu_1a4"]].sum().sum() / casos, 1))
    for p in PLANOS:
        print(f"{p} (%):", round(100 * sub[p].sum() / casos, 1))
    print("Unidade-semanas informadas:", int(unid_sem))
    print("Casos por unidade informante por semana:", round(casos / unid_sem, 2))


for ano in (2025, 2026):
    df = pd.read_parquet(raw / f"sivep_dda_{ano}.parquet")
    df = df[df["sem_epid_year"] == ano].copy()
    print(f"\n==================== {ano} ====================")

    pbs = df[df["municipio_ibge"] == COD_PBS].sort_values("sem_epid_week")

    ult = df["sem_epid_week"].max()
    faltando = sorted(set(range(1, ult + 1)) - set(pbs["sem_epid_week"]))
    print("Semanas sem registro em Parauapebas:", faltando)

    # Semana em que o número de unidades implantadas mudou
    mud = pbs.loc[pbs["nu_usaude_sem"].diff().fillna(0) != 0, ["sem_epid_week", "nu_usaude_sem"]]
    print("Mudanças no número de unidades implantadas:\n", mud.to_string(index=False))

    resumo(pbs, "Parauapebas")
    resumo(df[df["uf_ibge"] == 15], "Pará")
    resumo(df, "Brasil")

    # Conferência com a Nota Técnica da Anvisa (consulta em 24/10/2025)
    if ano == 2025:
        for se in (42, 43):
            acum = df.loc[df["sem_epid_week"] <= se, FAIXAS].sum().sum()
            print(f"Brasil acumulado até a SE {se}:", int(acum))
