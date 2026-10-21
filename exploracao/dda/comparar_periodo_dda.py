from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

raw = Path("../data/raw")
fig_dir = Path("../figuras")
fig_dir.mkdir(exist_ok=True)

COD_PBS = 150553
FAIXAS = ["nu_m1ano", "nu_1a4", "nu_5a9", "nu_10oumais", "nu_faixign"]
SE_MAX = 22

series = {}
for ano in (2025, 2026):
    df = pd.read_parquet(raw / f"sivep_dda_{ano}.parquet")
    df = df[df["sem_epid_year"] == ano].copy()
    df["casos"] = df[FAIXAS].sum(axis=1)

    per = df[df["sem_epid_week"] <= SE_MAX]
    print(f"\n===== {ano}, SE 1 a {SE_MAX} =====")
    for nome, sub in [
        ("Parauapebas", per[per["municipio_ibge"] == COD_PBS]),
        ("Pará", per[per["uf_ibge"] == 15]),
        ("Brasil", per),
    ]:
        casos = sub["casos"].sum()
        us = sub["nu_unidades_inf"].sum()
        print(f"{nome}: {int(casos)} casos | {round(casos / us, 2)} casos por unidade-semana")

    pbs = df[df["municipio_ibge"] == COD_PBS].sort_values("sem_epid_week")
    series[ano] = pbs.set_index("sem_epid_week")["casos"]

fig, ax = plt.subplots(figsize=(9, 4))
for ano, s in series.items():
    ax.plot(s.index, s.values, marker="o", markersize=3, label=str(ano))
ax.set_xlabel("Semana epidemiológica")
ax.set_ylabel("Casos de DDA")
ax.set_title("Casos semanais de DDA, Parauapebas, 2025–2026")
ax.legend()
ax.grid(alpha=0.3)
fig.text(
    0.01,
    0.01,
    "Fonte: Sivep-DDA/MS (Saldanha, 2026). 2026: dados preliminares até a SE 22.",
    fontsize=8,
)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(fig_dir / "dda_parauapebas_semanal.png", dpi=300)
print("\nFigura salva em figuras/dda_parauapebas_semanal.png")
