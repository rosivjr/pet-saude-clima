# 0009. Só AIH do tipo 1 contam como internação no SIH

**Status:** Aceita
**Registro:** 2026-10-18

## Contexto

A Autorização de Internação Hospitalar (AIH) tem tipos. A AIH do tipo 1 (normal) abre a internação. A do tipo 5 (longa permanência) é emitida para continuar uma internação que passou do limite de dias da AIH inicial. As duas aparecem no arquivo RD do SIH, identificadas pela coluna `IDENT`.

Contar todas as linhas do RD como internações contaria duas ou mais vezes o mesmo paciente internado por muito tempo. Em agravos agudos como os DRSAI, internações longas são raras, mas a regra precisa valer para todo o período e para todas as causas, inclusive o denominador de "todas as causas".

## Decisão

Só a AIH do tipo 1 conta como internação:

- `filtrar_aih_normal` (`src/transformacoes.py`) mantém as linhas com `IDENT` igual a `SIH_IDENT_NORMAL` ("1") e registra na proveniência quantas linhas de outros tipos foram descartadas;
- se a coluna `IDENT` faltar no arquivo, o filtro não é aplicado e o log registra um aviso;
- `src/validacao.py` confere com pandera que, depois do filtro, `IDENT` só tem o valor "1".

## Alternativas

- **Contar todas as AIH.** É mais simples, mas mede autorizações pagas, e não internações.
- **Juntar as AIH de um mesmo paciente.** Seria o método mais fiel, mas os arquivos públicos não trazem um identificador do paciente que permita a ligação.

## Consequências

- Quem conferir os números com outra tabulação do SIH precisa verificar se ela considera o tipo de AIH.
- Na execução de 20/10/2026, as 43.463 AIH de 2023-2026 eram todas do tipo 1, e o filtro não removeu nenhuma. Ele fica como proteção para as competências futuras.
- A regra vale para o indicador DRSAI e para o total de internações por todas as causas, que servem de comparação.

## Fonte

- Bittencourt, S. A.; Camacho, L. A. B.; Leal, M. C. O Sistema de Informação Hospitalar e sua aplicação na saúde coletiva. *Cadernos de Saúde Pública*, Rio de Janeiro, v. 22, n. 1, p. 19-30, 2006. O trecho sobre a AIH do tipo 5 está na p. 26.
- Ministério da Saúde. DATASUS. Notas técnicas do SIH/SUS (variável `IDENT`, tipo da AIH).
