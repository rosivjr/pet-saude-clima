# 0021. Número de unidades do Sivep-DDA acima de 100 vezes a mediana é erro de digitação

**Status:** Aceita
**Registro:** 2026-10-21

## Contexto

O Sivep-DDA registra, por semana epidemiológica e município, os casos de diarreia aguda e o número de unidades de saúde que informaram (`nu_unidades_inf`) entre as que deveriam informar (`nu_usaude_sem`). Esse número é o denominador da razão casos por unidade-semana e da completude da notificação em `dda/`.

Alguns registros trazem um número de unidades centenas de vezes maior que o habitual do próprio município, o que indica erro de digitação. Sem correção, um único valor desses distorce a soma nacional de unidades e, com ela, a razão casos por unidade-semana. Não há regra oficial de limpeza desse campo. Em 21/10/2026 foram consultados o Instrutivo para registro de dados no Sivep-DDA, o Guia de Vigilância em Saúde do Ministério da Saúde (6ª edição revisada, 2024, volume 1, capítulo "Doenças diarreicas agudas") e o PubMed (Sivep-DDA, MDDA e vigilância sentinela de diarreia no Brasil com qualidade de dados). O instrutivo diz que o número de unidades que atendem diarreia é cadastrado no início do ano, que a cada semana se digitam as unidades com MDDA implantada e as que informaram, e que o erro de digitação é corrigido pelo próprio município, refazendo o registro. Nenhuma das três fontes traz critério para valores implausíveis.

## Decisão

Em `dda/limpeza_dda.py` (`corrigir_unidades`), um valor de `nu_unidades_inf` ou de `nu_usaude_sem` maior que 100 vezes a mediana do mesmo município no ano é trocado por essa mediana. O múltiplo está em `config.DDA_LIMITE_MEDIANA_UNIDADES`. É um critério do projeto, sem fonte oficial, e a justificativa é a análise de sensibilidade abaixo.

## Sensibilidade

`dda/sensibilidade_limpeza.py` refaz o resultado do Brasil com quatro múltiplos (execução de 21/10/2026):

| Ano | Múltiplo | Casos por unidade-semana | Registros corrigidos (informantes / existentes) | Completude |
|---|---|---|---|---|
| 2025 | sem correção | 5,17 | — | — |
| 2025 | 10× | 5,35 | 110 / 151 | 82,6% |
| 2025 | 50× | 5,34 | 8 / 6 | 82,4% |
| 2025 | **100×** | **5,34** | **1 / 5** | **82,5%** |
| 2025 | 1000× | 5,34 | 1 / 2 | 82,4% |
| 2026 | sem correção | 5,97 | — | — |
| 2026 | 10× | 5,98 | 63 / 70 | 82,9% |
| 2026 | 50× | 5,97 | 6 / 3 | 82,7% |
| 2026 | **100×** | **5,97** | **0 / 3** | **82,8%** |
| 2026 | 1000× | 5,97 | 0 / 0 | 82,4% |

Informantes é `nu_unidades_inf`, numerador da completude e denominador da razão; existentes é `nu_usaude_sem`, denominador da completude. Em 2026, 1000× não corrige nada, e por isso 82,4% é também a completude sem correção.

De 50× a 1000×, a razão casos por unidade-semana não muda na segunda casa decimal: o que muda o resultado é corrigir o erro grosseiro; entre 50× e 1000× o múltiplo não pesa. Com 10×, a regra passa a corrigir mais de cem registros em 2025 e dezenas em 2026, que podem ser variações reais, por exemplo um município que ampliou a rede sentinela. 100× corrige, em 2025, o erro evidente de unidades informantes e 5 registros de unidades existentes; em 2026, nenhum registro de informantes e 3 de existentes. A correção de unidades existentes não mexe na razão casos por unidade-semana, só na completude.

## Alternativas

- **Sem correção.** Mantém um erro evidente que muda a razão de 2025 de 5,34 para 5,17.
- **Regra da mediana mais k desvios absolutos medianos (MAD).** É um método geral de detecção de valores extremos, mas também exige escolher k sem fonte específica para o Sivep-DDA, e pode marcar variações reais em municípios com poucas unidades.
- **Excluir o registro.** Perde os casos da semana, que não têm o erro.

## Consequências

- Os resultados de `dda/` dependem desse critério em 2025 (1 registro de unidades informantes e 5 de existentes) e em 2026 (3 registros de unidades existentes, que mudam só a completude, de 82,4% para 82,8%).
- `tests/test_limpeza_dda.py` confere a regra com valores feitos à mão.

## Fonte

- Ministério da Saúde. Instrutivo para registro de dados no Sivep-DDA (https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/dda/vigilancia-epidemiologica/formularios/sivep-dda-instrutivo-registro-de-dados.pdf): o número de unidades é informado pelo município no início de cada ano.
- Ministério da Saúde. Guia de Vigilância em Saúde, 6ª edição revisada, volume 1, 2024 (https://bvsms.saude.gov.br/bvs/publicacoes/guia_vigilancia_saude_6edrev_v1.pdf), capítulo "Doenças diarreicas agudas": trata da análise semanal dos dados do Sivep-DDA, sem critério para valores implausíveis.
- Análise de sensibilidade em `dda/sensibilidade_limpeza.py`.
