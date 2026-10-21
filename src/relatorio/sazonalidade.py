"""Seção de chuva e do padrão de cada mês: chuva, E. coli e internações."""

import pandas as pd

from src import config

from ._formato import numero, subtitulo, titulo


def secao_precipitacao(
    comparada: pd.DataFrame | None,
    chuva_mensal: pd.DataFrame | None,
    meta: dict | None,
) -> str:
    """
    Formata a chuva mensal e o padrão de cada mês do calendário.

    meta traz os metadados da série de chuva: fonte, modelo e ponto de grade.
    """
    linhas = [titulo("21. PRECIPITAÇÃO E SAZONALIDADE")]
    if comparada is None or chuva_mensal is None or chuva_mensal.empty:
        linhas.append("  Série de precipitação não disponível nesta execução.\n")
        return "\n".join(linhas)

    meta = meta or {}
    modelos = {
        "era5_land": ("ERA5-Land", "0,1°, cerca de 9 km"),
        "era5": ("ERA5", "0,25°, cerca de 25 km"),
    }
    modelo = meta.get("modelo", config.CLIMA_MODELO)
    nome, grade = modelos.get(modelo, (modelo, "resolução não informada"))
    linhas.append(
        f"Fonte: {meta.get('fonte', 'Open-Meteo')}, reanálise {nome} (ECMWF),\n"
        f"grade de {grade}. Ponto de grade: {meta.get('latitude_grade')}, "
        f"{meta.get('longitude_grade')}.\n"
        "Reanálise estima a chuva por modelo; não substitui estação\n"
        "meteorológica. Usada para descrever o padrão sazonal.\n"
    )

    linhas.append(subtitulo("Chuva acumulada por mês (mm)"))
    anos = sorted(chuva_mensal["ano"].unique())
    linhas.append("  Mês   " + "".join(f"{int(a):>9}" for a in anos))
    for mes in range(1, 13):
        valores = []
        for ano in anos:
            v = chuva_mensal[(chuva_mensal["ano"] == ano) & (chuva_mensal["mes"] == mes)]
            if v.empty or pd.isna(v["precipitacao_mm"].iloc[0]):
                valores.append(f"{'—':>9}")
            else:
                valores.append(f"{numero(v['precipitacao_mm'].iloc[0]):>9}")
        linhas.append(f"  {config.MESES_ABREV[mes]:<6}" + "".join(valores))

    linhas.append(subtitulo("Padrão de cada mês do calendário (anos do período somados)"))
    linhas.append(
        "  Lado a lado, sem estimar associação. Chuva e internações são\n"
        "  médias entre os anos; E. coli junta todas as amostras do mês.\n"
    )
    linhas.append(
        f"  {'Mês':<6}{'Chuva':>8}{'E. coli %':>11}  {'IC95%':<12}{'Amostras':>9}"
        f"{'Intern. DRSAI':>15}"
    )
    for _, reg in comparada.iterrows():
        chuva = numero(reg["chuva_media_mm"]) if pd.notna(reg["chuva_media_mm"]) else "—"
        if pd.notna(reg["ecoli_percentual"]):
            ecoli = numero(reg["ecoli_percentual"]) + "%"
            ic = f"{numero(reg['ecoli_ic_inferior'])}–{numero(reg['ecoli_ic_superior'])}"
        else:
            ecoli, ic = "—", ""
        internacoes = (
            numero(reg["internacoes_media"]) if pd.notna(reg["internacoes_media"]) else "—"
        )
        linhas.append(
            f"  {config.MESES_ABREV[int(reg['mes'])]:<6}{chuva:>8}{ecoli:>11}  {ic:<12}"
            f"{int(reg['ecoli_amostras']):>9}{internacoes:>15}"
        )

    linhas.append("\n  Coincidência entre meses não indica causa.")
    return "\n".join(linhas) + "\n"
