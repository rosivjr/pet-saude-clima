# 0013. RESULTADO do SISAGUA separado em uma coluna numérica e uma de texto

**Status:** Aceita
**Registro:** 2026-10-20

## Contexto

No SISAGUA, a coluna `RESULTADO` guarda o resultado de todos os parâmetros num campo de texto. Nos parâmetros físico-químicos (cloro residual livre, turbidez, pH) é um número com vírgula decimal ("0,92"). Nos microbiológicos (coliformes totais, *Escherichia coli*) é PRESENTE ou AUSENTE. Converter a coluna inteira para número perderia os resultados microbiológicos; tratá-la inteira como texto impediria comparar os físico-químicos com os limites da Portaria GM/MS nº 888/2021.

## Decisão

`padronizar_sisagua` (`src/transformacoes.py`) mantém `RESULTADO` e cria duas colunas a partir dela:

- `resultado_numerico`: `converter_decimal_brasileiro`, que troca a vírgula decimal por ponto e devolve NaN para o que não é número, como PRESENTE e AUSENTE. O ponto só é aceito como separador de milhar (decisão 0010);
- `resultado_texto`: o valor sem espaços nas pontas e em maiúsculas.

Cada indicador usa a coluna do seu tipo de parâmetro:

- físico-químicos: `resultado_numerico`. Amostras sem número legível ficam fora do denominador da conformidade (`avaliar_conformidade_agua`);
- microbiológicos: `resultado_texto`. PRESENTE conta como amostra com presença; o critério mensal da Portaria não é aplicado, porque as amostras são da vigilância. O denominador é o total de amostras do parâmetro (`avaliar_microbiologico`, `serie_anual_agua`, `src/indicadores/agua.py`).

## Alternativas

- **Uma coluna só, convertida para número.** Perde PRESENTE e AUSENTE.
- **Separar as amostras por parâmetro antes de converter.** Chega ao mesmo resultado, com uma etapa a mais e o risco de um parâmetro novo cair no grupo errado.

## Consequências

- Nos microbiológicos, um texto diferente de PRESENTE e AUSENTE entra no denominador e não conta como positivo. Quantos são aparece na seção de qualidade dos dados, na linha "Resultado microbiológico (presente/ausente)" (`src/qualidade.py`).
- Nos físico-químicos, a mesma seção mostra quantos resultados não puderam ser lidos como número ("Resultado numérico legível").
- O esquema pandera (`src/validacao.py`) confere que `resultado_texto` é texto.

## Fonte

- Ministério da Saúde. Portaria GM/MS nº 888, de 4 de maio de 2021.
- Decisão 0010, sobre o ponto decimal em `RESULTADO`.
