# 0014. Análise territorial da água pela área de abrangência, sem coordenadas

**Status:** Aceita
**Registro:** 2026-10-20

## Contexto

A Meta 1 do Eixo II pede a distribuição territorial da qualidade da água. O SISAGUA tem colunas de latitude e longitude, mas, na versão 2025–2026 do projeto, elas vieram vazias em todas as amostras de Parauapebas de 2025 (registro no antigo `docs/estado_projeto.md`, commit `169139c`). Os anos de 2023 e 2024 não foram conferidos.

O SISAGUA também traz a área de abrangência do ponto de coleta (`NO_AREA`), um texto que corresponde ao bairro ou à área atendida.

## Decisão

A análise territorial usa `NO_AREA`:

- `carregar_sisagua` (`src/carregadores.py`) lê `NO_AREA`, a categoria da área e o tipo de ponto de coleta, e não lê latitude nem longitude;
- `padronizar_sisagua` normaliza a grafia das áreas (`_normalizar_texto`), para que "Rio Verde" e "RIO VERDE" sejam a mesma área, e registra no log quantas amostras vieram sem área;
- as tabelas por área (`src/indicadores/territorio.py`) só usam as amostras com área preenchida, e áreas com poucas amostras ficam marcadas.

## Alternativas

- **Coordenadas de cada ponto.** Permitiriam mapa por ponto, mas não existem nos dados de 2025.
- **Geocodificar o nome da área.** Os nomes não seguem um cadastro oficial de bairros, e o erro de geocodificação entraria na análise sem como medi-lo.

## Consequências

- A distribuição é por área, não por ponto, e depende de como cada coleta foi registrada.
- A comparação entre áreas não controla o número de coletas por solução. O rodapé do relatório avisa que coletas repetidas na mesma solução ou área não são independentes e que os intervalos subestimam a incerteza.
- Pendente: conferir se as coordenadas vêm preenchidas em 2023 e 2024. Se vierem, rever esta decisão para esses anos.

## Fonte

- Projeto PET-Saúde CLIMA, Eixo II: Meta 1 (distribuição territorial).
- Registro sobre as coordenadas: `docs/estado_projeto.md` no commit `169139c`; o arquivo foi removido no commit `0d88e24`.
