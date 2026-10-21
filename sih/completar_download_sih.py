"""
Baixa, mês a mês, os arquivos RD de todas as UFs que faltam no cache do
PySUS, nas competências de config.SIH_COMPETENCIAS_NACIONAIS, com progresso
e tempo limite.

Cada arquivo baixado fica em data/raw/sih/proveniencia_sih_nacional.json
(comum.registro_sih); os registros de execuções anteriores são mantidos.
"""

import json
import multiprocessing as mp
import time
from datetime import datetime

import pysus

from sih import comum
from src import config, proveniencia

TEMPO_LIMITE = 300  # segundos por tentativa
TENTATIVAS = 3
PROVENIENCIA_NACIONAL = comum.PASTA_BRUTOS / "proveniencia_sih_nacional.json"


def consulta(uf: str, ano: int, mes: int) -> str:
    """Chamada ao PySUS de uma competência, como fica na proveniência."""
    return f"pysus.ftp.sih(state={uf}, year={ano}, month={mes}, group=RD)"


def baixar(uf: str, ano: int, mes: int) -> None:
    """Baixa uma competência para o cache do PySUS (roda num processo à parte)."""
    pysus.ftp.sih(state=uf, year=ano, month=mes, group="RD", source=config.PYSUS_SOURCE)


def gravar_proveniencia(baixados: list[dict]) -> None:
    """Junta os registros novos aos do JSON existente, um por arquivo, e grava."""
    anteriores = (
        json.loads(PROVENIENCIA_NACIONAL.read_text(encoding="utf-8"))["arquivos"]
        if PROVENIENCIA_NACIONAL.exists()
        else []
    )
    por_arquivo = {r["arquivo"]: r for r in anteriores} | {r["arquivo"]: r for r in baixados}
    PROVENIENCIA_NACIONAL.write_text(
        json.dumps(
            {
                "gerado_em": datetime.now(proveniencia.FUSO).isoformat(timespec="seconds"),
                "arquivos": sorted(por_arquivo.values(), key=lambda r: r["arquivo"]),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> None:
    faltando = [
        (uf, ano, mes)
        for uf in config.UFS
        for ano, meses in config.SIH_COMPETENCIAS_NACIONAIS.items()
        for mes in meses
        if not (config.PYSUS_PASTA_SIH / comum.nome_rd(uf, ano, mes)).exists()
    ]
    total = len(faltando)
    print(f"Arquivos faltando antes: {total}", flush=True)

    baixados = []
    for i, (uf, ano, mes) in enumerate(faltando, start=1):
        caminho = config.PYSUS_PASTA_SIH / comum.nome_rd(uf, ano, mes)
        for tentativa in range(1, TENTATIVAS + 1):
            print(f"[{i}/{total}] {caminho.name}: tentativa {tentativa}...", end=" ", flush=True)
            inicio = time.time()
            processo = mp.Process(target=baixar, args=(uf, ano, mes))
            processo.start()
            processo.join(TEMPO_LIMITE)
            if processo.is_alive():
                processo.terminate()
                processo.join()
                print("tempo esgotado", flush=True)
            elif caminho.exists():
                print(f"ok ({time.time() - inicio:.0f} s)", flush=True)
                baixados.append(comum.registro_sih(caminho, consulta(uf, ano, mes)))
                break
            else:
                print("não disponível", flush=True)
            time.sleep(5)

    if baixados:
        comum.PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
        gravar_proveniencia(baixados)
        print(f"\nProveniência de {len(baixados)} arquivo(s) em {PROVENIENCIA_NACIONAL}")

    ainda = [
        comum.nome_rd(*competencia)
        for competencia in faltando
        if not (config.PYSUS_PASTA_SIH / comum.nome_rd(*competencia)).exists()
    ]
    print(f"\nArquivos ainda faltando: {len(ainda)}")
    for nome_faltando in ainda:
        print(" -", nome_faltando)


if __name__ == "__main__":
    main()
