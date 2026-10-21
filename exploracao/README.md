# Exploração

Scripts usados para testar dados e caminhos durante o relatório DDA,
hepatite A e saneamento. Ficam versionados para registrar o que foi testado.
**Não são mantidos e não precisam rodar com o código atual**: os caminhos e
imports são os da época. Se algum for reaproveitado, ele continua obrigado
a imprimir só agregados.

| Script | O que testou | Substituído por |
|---|---|---|
| `dda/inspecionar_dda.py` | Esquema, número de linhas e proveniência dos parquets do Sivep-DDA | — |
| `dda/completar_dda.py` | Semanas sem registro em Parauapebas, mudança no número de unidades implantadas, Parauapebas × Pará × Brasil sem correção das unidades e conferência com a Nota Técnica da Anvisa (consulta em 24/10/2025) | `dda/resumo_final_dda.py`, com a correção de `dda/limpeza_dda.py` |
| `dda/comparar_periodo_dda.py` | Casos e casos por unidade-semana nas SE 1 a 22 de 2025 e 2026, e a primeira versão da figura semanal | Figura 1 de `dda/figuras_dda.py`; `dda/sensibilidade_dda.py` |
| `sih/diagnostico_sih.py` | Quais arquivos RD o PySUS devolvia para cada UF e ano, e quantos estavam no disco | `sih/completar_download_sih.py` |
| `sih/diagnostico_faltantes.py` | Download dos arquivos RD que faltavam, um a um | `sih/completar_download_sih.py` |

Cuidados ao rodar:

- `sih/diagnostico_sih.py` e `sih/diagnostico_faltantes.py` disparam downloads do SIH.

`sinan/colunas_sinan.py`, que testou qual coluna do Sinan hepatites indica o
vírus, foi apagado porque lia o arquivo nacional inteiro, o que o CONTRIBUTING.md
proíbe. Ele continua no histórico do git (commit `59bc7ea`). O critério que
saiu dele está em `config.SINAN_HAV_VIRUS_A`, com a fonte.
