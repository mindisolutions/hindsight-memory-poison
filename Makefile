PY ?= python3
HINDSIGHT_BASE_URL ?= http://localhost:8890

.PHONY: help lint aggregate phase1 phase2 probes benchmark all

help:
	@echo "Hindsight Memory Poisoning — targets:"
	@echo "  lint        run pylint on scripts/"
	@echo "  aggregate   regenerate reports/summary.json (Fisher, Wilson, Cohen's h)"
	@echo "  phase1      run Phase-1 security probes (bank isolation / reflect injection / entity poisoning)"
	@echo "  phase2      run Phase-2 security probes (proof-count / recency / metadata-null)"
	@echo "  benchmark   run the config-driven benchmark suite (benchmarks.yaml)"
	@echo "  all         lint + aggregate + phase1 + phase2"

lint:
	$(PY) -m pylint scripts/ --rcfile=.pylintrc

aggregate:
	$(PY) scripts/aggregate_report.py

phase1:
	HINDSIGHT_BASE_URL=$(HINDSIGHT_BASE_URL) $(PY) scripts/12_security_probes.py

phase2:
	HINDSIGHT_BASE_URL=$(HINDSIGHT_BASE_URL) $(PY) scripts/13_phase2_probes.py

benchmark:
	HINDSIGHT_BASE_URL=$(HINDSIGHT_BASE_URL) $(PY) scripts/benchmark.py benchmarks.yaml

all: lint aggregate phase1 phase2
