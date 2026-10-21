# 0004. CID comparado pelos três primeiros caracteres e um único grupo por internação

**Status:** Aceita
**Registro:** 2026-10-18

## Contexto

A classificação de DRSAI da FUNASA (2010) é definida por categorias da CID-10, com três caracteres (por exemplo, A09). O SIH grava o diagnóstico sem ponto e com o quarto caractere, como `A090` para A09.0. O SIM faz o mesmo com a causa básica. Comparar o código inteiro com a lista da FUNASA não encontraria nenhum caso.

Os grupos de `GRUPOS_AGRAVO` (feco-oral, inseto vetor, contato com água, higiene, geo-helmintos e teníases, além dos grupos fora do DRSAI) servem para somar internações. Se um código pertencesse a dois grupos, a mesma internação seria contada duas vezes no indicador DRSAI.

## Decisão

- O código CID-10 é comparado pelos três primeiros caracteres, em maiúsculas: `_classificar_grupo_agravo` (`src/transformacoes.py`) usa `cid[:3]`. Códigos com menos de três caracteres ou ausentes ficam sem grupo.
- Cada internação recebe um único grupo, a partir do diagnóstico principal (`DIAG_PRINC`) no SIH e da causa básica (`CAUSABAS`) no SIM. Diagnósticos secundários não são usados.
- Nenhum código pode estar em mais de um grupo. `tests/test_config.py` falha se houver código repetido em `GRUPOS_AGRAVO`.
- O indicador DRSAI soma só os grupos de `GRUPOS_DRSAI`. Arboviroses fora da lista da FUNASA, códigos usados só na sensibilidade e o contexto climático aparecem em blocos separados e nunca entram no total.

A tabela de códigos em `docs/metodos.md` (seção "Variáveis (item 7)") é gerada a partir do config e conferida por `tests/test_documentacao.py`.

## Alternativas

- **Comparar o código completo, com quatro caracteres.** Permitiria escolher subcategorias, mas a lista da FUNASA não desce a esse nível, e seria preciso enumerar todas as subcategorias de cada categoria.
- **Usar também os diagnósticos secundários.** Captaria mais casos, mas o SIH da AIH reduzida nem sempre traz os secundários preenchidos, e uma internação poderia cair em vários grupos.
- **Permitir mais de um grupo por internação.** Descreveria melhor casos com mais de uma doença, mas exigiria regras de desempate para não contar a internação duas vezes no total.

## Consequências

- Todas as subcategorias de uma categoria entram juntas. Por exemplo, todo A09 conta como feco-oral, inclusive A09.9, de origem não especificada.
- A dengue usa A90, A91 e A97 (CID-10 versão 2019) para não perder casos durante a troca de versão nos sistemas.
- A internação de um paciente com diarreia como diagnóstico secundário não é contada. Isso tende a subestimar a carga de DRSAI, e a limitação vale para todos os anos da série.
- Como cada internação tem um grupo só, a soma dos grupos é igual ao total de internações DRSAI.

## Fonte

- Fundação Nacional de Saúde (FUNASA). *Impactos na saúde e no Sistema Único de Saúde decorrentes de agravos relacionados a um saneamento ambiental inadequado*. Brasília: Funasa, 2010.
- Cairncross, S.; Feachem, R. *Environmental health engineering in the tropics*. 2. ed. Chichester: John Wiley & Sons, 1993.
- Benchimol, E. I. et al. (2015). RECORD statement, itens 6.1 e 7.1 (códigos usados para selecionar a população e definir os desfechos).
