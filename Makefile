.PHONY: format lint typecheck test quality-gate deps-direct deps-tree deps-outdated deps-audit deps-report audit-deps serve

format:
	ruff format .
	ruff check . --fix

lint:
	ruff check .

typecheck:
	mypy src/ tests/

test:
	pytest tests/

quality-gate: format lint typecheck test

deps-direct:
	@python -c "import pathlib, tomllib; data = tomllib.loads(pathlib.Path('pyproject.toml').read_text()); runtime = data.get('project', {}).get('dependencies', []); dev = data.get('dependency-groups', {}).get('dev', []); print('Runtime dependencies (project.dependencies):'); [print(f'  - {dep}') for dep in runtime] or None; print('\\nDev dependencies (dependency-groups.dev):'); [print(f'  - {dep}') for dep in dev] or None"

deps-tree:
	uv tree --frozen

deps-outdated:
	uv tree --frozen --depth 1 --outdated

deps-audit:
	mkdir -p .tmp
	uv export --frozen --no-hashes --format requirements-txt -o .tmp/requirements-audit.txt
	uvx --from pip-audit pip-audit -r .tmp/requirements-audit.txt

deps-report: deps-direct deps-outdated deps-audit

serve:
	python scripts/serve_dashboard.py
