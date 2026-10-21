# 0016. População de referência: estimativas do IBGE e 2023 por interpolação

**Status:** Aceita
**Registro:** 2026-10-20

## Contexto

A população de cada ano é o denominador de todas as taxas do estudo, pela pessoa-tempo (decisão 0002). O IBGE não publicou estimativa municipal em 2022, ano do Censo, nem em 2023: a série da Tabela SIDRA 6579 pula de 2021 para 2024. Para Parauapebas em 2023, primeiro ano do período, não há valor oficial.

## Decisão

Em `src/config.py` (`POPULACAO_ANUAL`, com a fonte de cada ano em `POPULACAO_FONTE`):

- 2024, 2025 e 2026: estimativas do IBGE publicadas no Diário Oficial da União, com referência em 1º de julho;
- 2023: interpolação geométrica entre o Censo Demográfico 2022 e a estimativa de 2024, tratando os dois como pontos de meio de ano: P2023 = raiz(P2022 × P2024).

## Alternativas

- **Série da Ripsa/CGIAE/SVSA/MS, no TabNet do DATASUS.** Tem valor para 2023, mas é outra fonte e outro método; pode substituir a interpolação se a equipe preferir.
- **População do Censo 2022 em todos os anos.** Era o método da versão anterior; ignora o crescimento do município ao longo do período.

## Consequências

- A população de 2023 é um valor calculado pelo projeto, não oficial, e precisa constar nos métodos. O cabeçalho do relatório mostra a fonte de cada ano, e o rodapé repete a ressalva.
- O teste `test_2023_e_media_geometrica_censo_2024` (`tests/test_config.py`) confere a fórmula e que o valor fica entre o Censo 2022 e a estimativa de 2024.

## Fonte

- IBGE. Censo Demográfico 2022.
- IBGE. Estimativas da População 2024, 2025 e 2026 (endereços em `src/config.py`).
- Decisão 0002, sobre a pessoa-tempo.
