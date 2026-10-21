"""Confere quais arquivos RD o PySUS retornou para cada UF e ano."""

from pathlib import Path

from pysus import sih

UFS = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
]
PERIODOS = {2025: list(range(1, 13)), 2026: list(range(1, 7))}

primeiro = True
problemas = 0
for uf in UFS:
    for ano, meses in PERIODOS.items():
        caminhos = sih(state=uf, year=ano, month=meses, group="RD")
        nomes = {Path(c).name for c in caminhos}
        if primeiro:
            print("Exemplo de nome retornado:", sorted(nomes)[:2])
            primeiro = False
        esperado = {f"RD{uf}{str(ano)[2:]}{m:02d}.parquet" for m in meses}
        faltam = sorted(esperado - nomes)
        extras = sorted(nomes - esperado)
        if faltam or extras:
            problemas += 1
            print(f"{uf} {ano}: retornou {len(nomes)} | faltam {faltam} | extras {extras}")

print(f"\nCombinações UF/ano com problema: {problemas} de {len(UFS) * len(PERIODOS)}")

# Arquivos RD que existem no disco
pasta = Path.home() / "pysus/downloads/ducklake/sih"
no_disco = sorted(p.name for p in pasta.glob("RD*.parquet"))
print(f"Arquivos RD no disco: {len(no_disco)} (esperado: {27 * 18})")
