"""
Baixa o SIH-RD do Pará pelo PySUS 2.x, nos anos de config.DDA_ANOS até
config.SIH_ULTIMA_COMPETENCIA, e inspeciona as colunas.

O corte é o mesmo de carregadores.carregar_sih: para estender a extração,
troque a constante e rode make baixar-sih (docs/dados.md).
"""

import json
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq
from pysus import sih

from sih import comum
from src import config, proveniencia
from src.carregadores import ERROS_PYSUS


def main() -> None:
    comum.PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)

    # Download mês a mês (meses ainda não publicados são registrados como ausentes)
    arquivos, ausentes = [], []
    for ano in config.DDA_ANOS:
        for mes in range(1, 13):
            if (ano, mes) > config.SIH_ULTIMA_COMPETENCIA:
                break
            consulta = f"pysus.sih(state={config.MUNICIPIO_UF}, year={ano}, month={mes})"
            try:
                caminhos = sih(
                    state=config.MUNICIPIO_UF, year=ano, month=mes, source=config.PYSUS_SOURCE
                )
                arquivos.extend(comum.registro_sih(Path(c), consulta) for c in caminhos)
                print(f"{ano}-{mes:02d}: {len(caminhos)} arquivo(s)")
            except (*ERROS_PYSUS, ValueError) as erro:  # PySUS, rede/FTP, parâmetro
                ausentes.append(f"{ano}-{mes:02d}")
                print(f"{ano}-{mes:02d}: não disponível ({type(erro).__name__})")

    print("\nMeses ausentes:", ausentes)

    # gerado_em é a hora desta execução; a do download de cada arquivo está nele.
    comum.PROVENIENCIA.write_text(
        json.dumps(
            {
                "gerado_em": datetime.now(proveniencia.FUSO).isoformat(timespec="seconds"),
                "meses_ausentes": ausentes,
                "arquivos": arquivos,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    if arquivos:
        # Só o esquema, sem ler os dados
        esquema = pq.read_schema(arquivos[0]["cache_pysus"])
        print("\nArquivo inspecionado:", arquivos[0]["cache_pysus"])
        print("Linhas x colunas:", (arquivos[0]["linhas"], len(esquema.names)))
        print("Colunas:", esquema.names)


if __name__ == "__main__":
    main()
