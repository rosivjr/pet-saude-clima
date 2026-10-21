"""Testa o download dos arquivos RD que realmente faltam."""

from pathlib import Path

import pysus

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
PERIODOS = {2025: range(1, 13), 2026: range(1, 7)}
PASTA = Path.home() / "pysus/downloads/ducklake/sih"

faltando = [
    (uf, ano, mes)
    for uf in UFS
    for ano, meses in PERIODOS.items()
    for mes in meses
    if not (PASTA / f"RD{uf}{str(ano)[2:]}{mes:02d}.parquet").exists()
]

print(f"Faltando: {len(faltando)}")
print("Lista completa:", [f"{uf}-{ano}-{mes:02d}" for uf, ano, mes in faltando])

# Quantos faltam por UF e por ano
por_uf = {}
for uf, ano, _ in faltando:
    por_uf.setdefault(f"{uf} {ano}", 0)
    por_uf[f"{uf} {ano}"] += 1
print("\nFaltantes por UF e ano:", por_uf)

# Testar os três primeiros
for uf, ano, mes in faltando[:3]:
    alvo = f"RD{uf}{str(ano)[2:]}{mes:02d}"
    print(f"\n===== {alvo} =====")
    retorno = pysus.ftp.sih(state=uf, year=ano, month=mes, group="RD")
    print("Retorno:", retorno)
    print("Arquivos com nome parecido em ~/pysus:")
    for p in (Path.home() / "pysus").rglob(f"{alvo}*"):
        print(" -", p, f"({p.stat().st_size} bytes)")
    print(f"Arquivos RD{uf} de {ano} na pasta:")
    for p in sorted(PASTA.glob(f"RD{uf}{str(ano)[2:]}*")):
        print(" -", p.name)
