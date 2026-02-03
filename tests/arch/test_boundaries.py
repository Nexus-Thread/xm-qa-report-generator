"""Architecture boundary tests for hexagonal layering rules."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

PACKAGE_NAME = "qa_report_generator"
LAYER_PREFIXES = {
    "domain": f"{PACKAGE_NAME}.domain",
    "application": f"{PACKAGE_NAME}.application",
    "adapters": f"{PACKAGE_NAME}.adapters",
    "plugins": f"{PACKAGE_NAME}.plugins",
}


def _source_root() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / PACKAGE_NAME


def _module_name(module_path: Path) -> str:
    relative = module_path.relative_to(_source_root())
    return ".".join([PACKAGE_NAME, *relative.with_suffix("").parts])


def _resolve_relative_import(current_module: str, level: int, module: str | None) -> str | None:
    if level == 0:
        return module

    parts = current_module.split(".")
    if level > len(parts):
        return None

    base_parts = parts[:-level]
    if module:
        base_parts.extend(module.split("."))
    return ".".join(base_parts)


def _iter_python_files() -> Iterable[Path]:
    source_root = _source_root()
    return source_root.rglob("*.py")


def _collect_internal_imports(module_path: Path) -> set[str]:
    module_name = _module_name(module_path)
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PACKAGE_NAME):
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_relative_import(module_name, node.level, node.module)
            if resolved and resolved.startswith(PACKAGE_NAME):
                imports.add(resolved)

    return imports


def _layer_for(module_name: str) -> str | None:
    for layer, prefix in LAYER_PREFIXES.items():
        if module_name.startswith(prefix):
            return layer
    return None


def _find_layer_imports(layer_name: str) -> dict[str, set[str]]:
    modules: dict[str, set[str]] = {}
    for module_path in _iter_python_files():
        module_name = _module_name(module_path)
        if _layer_for(module_name) != layer_name:
            continue
        modules[module_name] = _collect_internal_imports(module_path)
    return modules


def _format_violations(violations: list[tuple[str, str]]) -> str:
    return "\n".join(f"- {module} imports {imported}" for module, imported in violations)


def test_domain_does_not_import_outward() -> None:
    """Domain modules must not depend on application, adapters, or plugins."""
    banned_prefixes = (
        LAYER_PREFIXES["application"],
        LAYER_PREFIXES["adapters"],
        LAYER_PREFIXES["plugins"],
    )
    violations = [
        (module, imported) for module, imports in _find_layer_imports("domain").items() for imported in imports if imported.startswith(banned_prefixes)
    ]

    assert not violations, _format_violations(violations)


def test_application_does_not_import_adapters_or_plugins() -> None:
    """Application modules may depend on domain, not adapters/plugins."""
    banned_prefixes = (LAYER_PREFIXES["adapters"], LAYER_PREFIXES["plugins"])
    violations = [
        (module, imported) for module, imports in _find_layer_imports("application").items() for imported in imports if imported.startswith(banned_prefixes)
    ]

    assert not violations, _format_violations(violations)


def test_plugins_do_not_import_adapters() -> None:
    """Plugin modules may depend on domain/application, not adapters."""
    banned_prefixes = (LAYER_PREFIXES["adapters"],)
    violations = [
        (module, imported) for module, imports in _find_layer_imports("plugins").items() for imported in imports if imported.startswith(banned_prefixes)
    ]

    assert not violations, _format_violations(violations)


def test_adapters_do_not_import_other_adapters() -> None:
    """Adapters must not depend on other adapters; share via application/domain."""
    adapter_prefix = LAYER_PREFIXES["adapters"]
    violations: list[tuple[str, str]] = []

    for module, imports in _find_layer_imports("adapters").items():
        violations.extend((module, imported) for imported in imports if imported.startswith(adapter_prefix) and imported != module)

    assert not violations, _format_violations(violations)


def test_adapters_do_not_import_plugins() -> None:
    """Adapters must not depend on plugins; share via application/domain."""
    plugin_prefix = LAYER_PREFIXES["plugins"]
    violations = [
        (module, imported) for module, imports in _find_layer_imports("adapters").items() for imported in imports if imported.startswith(plugin_prefix)
    ]

    assert not violations, _format_violations(violations)
