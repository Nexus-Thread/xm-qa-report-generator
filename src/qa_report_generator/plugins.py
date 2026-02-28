"""Plugin discovery utilities."""

from __future__ import annotations

import importlib
import logging

LOGGER = logging.getLogger(__name__)


def discover_plugins(plugin_modules: tuple[str, ...]) -> None:
    """Import plugin modules configured by the user."""
    for module_name in plugin_modules:
        importlib.import_module(module_name)
        LOGGER.info("Loaded plugin module", extra={"component": __name__, "plugin_module": module_name})
