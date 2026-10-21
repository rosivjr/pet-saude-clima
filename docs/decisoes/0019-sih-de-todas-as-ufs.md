# 0019. SIH lido em todas as UFs, para contar residentes internados fora do Pará

**Status:** Proposta (para a versão publicada; até lá, vale como limitação)
**Registro:** 2026-10-21

## Contexto

O DATASUS organiza o SIH/SUS (AIH reduzida, RD) em arquivos mensais pela UF do hospital. `carregar_sih` (`src/carregadores.py`) lê só os arquivos do Pará e filtra a residência (`MUNIC_RES`). A internação de um residente de Parauapebas num hospital de outra UF, por exemplo no Tocantins ou no Maranhão, fica fora do relatório.

Isso apareceu na diferença entre dois scripts de `sih/`, que usam os mesmos critérios (AIH do tipo 1, ano por `DT_INTER`, residência por `MUNIC_RES`) e só leem arquivos diferentes:

| Ano de internação | `verificar_sih.py` (só RDPA) | `sih_nacional.py` (27 UFs) | Diferença |
|---|---|---|---|
| 2025 | 13.015 | 13.207 | 192 (1,5%) |
| 2026, até junho | 5.863 | 5.930 | 67 (1,1%) |

Os dois seguem a decisão 0009 e o recorte por `DT_INTER` (decisão 0003). A diferença é toda de residentes internados em outras UFs (conferido em 21/10/2026, contando por UF do arquivo).

## Decisão proposta

`carregar_sih` passa a ler os arquivos RD de todas as UFs (`config.UFS`) nas competências de `ANOS`, com o mesmo filtro de residência aplicado arquivo a arquivo, para não acumular as UFs na memória.

## Consequências, se aprovada

- Todas as taxas de internação sobem um pouco (cerca de 1% a 1,5% no total; nos grupos DRSAI, a medir).
- Exige baixar o SIH de 2023 e 2024 das outras 26 UFs: 624 arquivos (26 UFs × 24 meses); os do Pará e os de 2025 e 2026 já estão no cache. A primeira execução fica muito mais longa; as seguintes leem do cache (`docs/dados.md`).
- A proveniência passa a listar os arquivos de todas as UFs.

## Até a aprovação

A perda fica registrada como limitação, com o tamanho medido: em `docs/metodos.md` (Limitações), nas ressalvas do relatório e em `config.SIH_RESIDENTES_FORA_DO_PARA`. Os números do relatório continuam os de agora.

## Fonte

- Decisões 0003 e 0009.
- Ministério da Saúde. DATASUS. Notas técnicas do SIH/SUS: arquivos RD por UF do estabelecimento; `MUNIC_RES`, município de residência.
