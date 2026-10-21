import json
from pathlib import Path

import pyarrow.parquet as pq

raw = Path("../data/raw")

# A proveniência (URL, data do download, linhas, SHA-256) é gravada por
# baixar_dda.py no momento do download; aqui ela só é lida.
for ano in (2025, 2026):
    arq = raw / f"sivep_dda_{ano}.parquet"
    prov_caminho = raw / f"{arq.stem}_proveniencia.json"

    print(f"\n===== {ano} =====")
    if prov_caminho.exists():
        prov = json.loads(prov_caminho.read_text())
        print("Origem:", prov.get("origem", "não registrada"))
        print("Baixado em:", prov.get("baixado_em", "não registrado"))
    else:
        print("Sem proveniência: baixe de novo com baixar_dda.py.")

    # Só o esquema e o número de linhas; nenhum registro individual é mostrado.
    meta = pq.ParquetFile(arq)
    print("Linhas x colunas:", (meta.metadata.num_rows, meta.metadata.num_columns))
    print("\nColunas e tipos:")
    print(meta.schema_arrow.to_string(show_schema_metadata=False))
