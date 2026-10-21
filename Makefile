# Atalhos do projeto. Rode a partir da raiz: make <alvo>.
# Os alvos de download ficam à parte, para dda, sih e sinan não baixarem tudo de novo.

PY := uv run python
CODEBOOK_DDA := data/interim/dda_metadata/sivep_dda_codebook.csv

.PHONY: testes lint relatorio dda sih sinan baixar-dda baixar-sih baixar-sinan

testes:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

relatorio:
	$(PY) main.py > relatorio.txt

# Relatório DDA (Sivep-DDA)
dda: $(CODEBOOK_DDA)
	$(PY) -m dda.extrair_dda
	$(PY) -m dda.resumo_final_dda
	$(PY) -m dda.sensibilidade_dda
	$(PY) -m dda.sensibilidade_limpeza
	$(PY) -m dda.figuras_dda

# A Figura 4 de sih/figuras_sih.py lê a tabela gravada por sih_nacional.
sih:
	$(PY) -m sih.contar_sih
	$(PY) -m sih.verificar_sih
	$(PY) -m sih.sih_nacional
	$(PY) -m sih.figuras_sih

sinan:
	$(PY) -m sinan.hepatite_a_sinan

# O dicionário é extraído do zip que já está em data/raw, sem download.
$(CODEBOOK_DDA):
	$(PY) -c "from dda import comum; print(comum.extrair_dicionario())"

baixar-dda:
	$(PY) -m dda.baixar_dda

baixar-sih:
	$(PY) -m sih.baixar_sih
	$(PY) -m sih.completar_download_sih

# Copia o Sinan hepatites do cache do PySUS para data/raw/sinan, sem sobrescrever.
baixar-sinan:
	$(PY) -m sinan.baixar_sinan
