"""Plugin registry system for parsers, writers, and hooks.

This module provides three registries:
- ParserRegistry: Register custom test report parsers
- WriterRegistry: Register custom report output writers
- HookRegistry: Register lifecycle hooks for report generation events
"""

import logging
from collections.abc import Callable, Iterable
from importlib import import_module
from importlib.metadata import entry_points
from typing import Any, TypeVar

from qa_report_generator.application.ports.output import ReportParser, ReportWriter

logger = logging.getLogger(__name__)

# Type variables for generic registry
T = TypeVar("T")


class ParserRegistry:
    """Registry for test report parser plugins.

    Register custom parsers that implement the ReportParser interface
    to support different test report formats (e.g., pytest-json, junit-xml).
    """

    _parsers: dict[str, type[ReportParser]] = {}

    @classmethod
    def register(cls, name: str, parser_class: type[ReportParser]) -> None:
        """Register a parser plugin.

        Args:
            name: Unique identifier (e.g., "pytest-json", "junit-xml")
            parser_class: Class implementing the ReportParser interface

        """
        if name in cls._parsers:
            logger.warning("Parser '%s' already registered, overwriting", name)

        cls._parsers[name] = parser_class
        logger.info("Registered parser plugin: %s -> %s", name, parser_class.__name__)

    @classmethod
    def get(cls, name: str) -> type[ReportParser] | None:
        """Get a registered parser by name.

        Args:
            name: Parser identifier

        Returns:
            Parser class if found, None otherwise

        """
        return cls._parsers.get(name)

    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered parser names.

        Returns:
            List of registered parser identifiers

        """
        return list(cls._parsers.keys())

    @classmethod
    def list_plugins(cls) -> dict[str, type[ReportParser]]:
        """Return a mapping of registered parser names to classes."""
        return dict(cls._parsers)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered parsers (useful for testing)."""
        cls._parsers.clear()


class WriterRegistry:
    """Registry for report writer plugins.

    Register custom writers that implement the ReportWriter interface
    to support different output formats (e.g., markdown, html, json).
    """

    _writers: dict[str, type[ReportWriter]] = {}

    @classmethod
    def register(cls, name: str, writer_class: type[ReportWriter]) -> None:
        """Register a writer plugin.

        Args:
            name: Unique identifier (e.g., "markdown", "html", "json")
            writer_class: Class implementing the ReportWriter interface

        """
        if name in cls._writers:
            logger.warning("Writer '%s' already registered, overwriting", name)

        cls._writers[name] = writer_class
        logger.info("Registered writer plugin: %s -> %s", name, writer_class.__name__)

    @classmethod
    def get(cls, name: str) -> type[ReportWriter] | None:
        """Get a registered writer by name.

        Args:
            name: Writer identifier

        Returns:
            Writer class if found, None otherwise

        """
        return cls._writers.get(name)

    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered writer names.

        Returns:
            List of registered writer identifiers

        """
        return list(cls._writers.keys())

    @classmethod
    def list_plugins(cls) -> dict[str, type[ReportWriter]]:
        """Return a mapping of registered writer names to classes."""
        return dict(cls._writers)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered writers (useful for testing)."""
        cls._writers.clear()


class HookRegistry:
    """Registry for lifecycle hooks during report generation.

    Hook Points & Context Data:
    - pre_parse: Before parsing (context: {"filepath": Path})
    - post_parse: After parsing (context: {"filepath": Path, "metrics": RunMetrics})
    - pre_generate: Before LLM generation (context: {"metrics": RunMetrics})
    - post_generate: After generation (context: {"metrics": RunMetrics, "reports": dict})
    - post_write: After writing reports (context: {"output_dir": Path, "summary_path": Path})
    """

    _hooks: dict[str, list[Callable]] = {
        "pre_parse": [],
        "post_parse": [],
        "pre_generate": [],
        "post_generate": [],
        "post_write": [],
    }

    @classmethod
    def register(cls, hook_point: str, hook_func: Callable) -> None:
        """Register a hook function.

        Args:
            hook_point: Hook point name (e.g., "post_write")
            hook_func: Callable that accepts a context dict

        Raises:
            ValueError: If hook_point is invalid

        """
        if hook_point not in cls._hooks:
            valid = ", ".join(cls._hooks.keys())
            msg = f"Invalid hook point '{hook_point}'. Valid options: {valid}"
            logger.error(msg)
            raise ValueError(msg)

        cls._hooks[hook_point].append(hook_func)
        logger.info("Registered hook: %s -> %s", hook_point, hook_func.__name__)

    @classmethod
    def get_hooks(cls, hook_point: str) -> list[Callable]:
        """Get all hooks for a specific hook point.

        Args:
            hook_point: Hook point name

        Returns:
            List of registered hook functions

        """
        return cls._hooks.get(hook_point, [])

    @classmethod
    def list_hooks(cls) -> dict[str, list[Callable]]:
        """Return all registered hooks grouped by hook point."""
        return {hook_point: list(hooks) for hook_point, hooks in cls._hooks.items()}

    @classmethod
    def execute_hooks(cls, hook_point: str, context: dict[str, Any]) -> None:
        """Execute all hooks for a hook point.

        Args:
            hook_point: Hook point name
            context: Context data passed to each hook function

        """
        hooks = cls.get_hooks(hook_point)
        if not hooks:
            return

        logger.debug("Executing %d hook(s) for %s", len(hooks), hook_point)

        for hook in hooks:
            try:
                hook(context)
            except Exception as e:
                # Log error but don't fail the entire process
                logger.exception(
                    "Hook '%s' failed at %s: %s",
                    hook.__name__,
                    hook_point,
                    e,
                )

    @classmethod
    def list_hook_points(cls) -> list[str]:
        """List all available hook points.

        Returns:
            List of valid hook point names

        """
        return list(cls._hooks.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered hooks (useful for testing)."""
        for hook_list in cls._hooks.values():
            hook_list.clear()


PLUGIN_ENTRYPOINT_GROUPS = {
    "parsers": "qa_report_generator.parsers",
    "writers": "qa_report_generator.writers",
    "hooks": "qa_report_generator.hooks",
}


def discover_plugins(plugin_modules: Iterable[str] | None = None) -> None:
    """Discover plugins via entry points and optional module imports.

    Args:
        plugin_modules: Optional iterable of module paths to import, ensuring
            decorator-based plugin registrations are executed.

    """
    entrypoint_data = entry_points()
    for group in PLUGIN_ENTRYPOINT_GROUPS.values():
        for entrypoint in entrypoint_data.select(group=group):
            try:
                entrypoint.load()
                logger.info(
                    "Loaded plugin entry point: %s -> %s",
                    group,
                    entrypoint.name,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception(
                    "Failed to load plugin entry point '%s' in group '%s': %s",
                    entrypoint.name,
                    group,
                    exc,
                )

    if not plugin_modules:
        return

    for module_path in plugin_modules:
        try:
            import_module(module_path)
            logger.info("Imported plugin module: %s", module_path)
        except Exception as exc:
            logger.exception("Failed to import plugin module '%s': %s", module_path, exc)


# Decorator functions for easy registration


def register_parser(name: str) -> Callable[[type[ReportParser]], type[ReportParser]]:
    """Register a parser plugin using a decorator.

    Example:
        @register_parser("junit-xml")
        class JUnitParser(ReportParser):
            def parse(self, filepath: Path) -> RunMetrics:
                ...

    Args:
        name: Unique parser identifier

    Returns:
        Decorator function

    """

    def decorator(parser_class: type[ReportParser]) -> type[ReportParser]:
        ParserRegistry.register(name, parser_class)
        return parser_class

    return decorator


def register_writer(name: str) -> Callable[[type[ReportWriter]], type[ReportWriter]]:
    """Register a writer plugin using a decorator.

    Example:
        @register_writer("html")
        class HTMLWriter(ReportWriter):
            def save_reports(self, facts, output_dir, narrative_generator, prompt_template_path=None):
                ...

    Args:
        name: Unique writer identifier

    Returns:
        Decorator function

    """

    def decorator(writer_class: type[ReportWriter]) -> type[ReportWriter]:
        WriterRegistry.register(name, writer_class)
        return writer_class

    return decorator


def register_hook(hook_point: str) -> Callable[[Callable], Callable]:
    """Register a hook function using a decorator.

    Example:
        @register_hook("post_write")
        def notify_teams(context: dict) -> None:
            summary_path = context["summary_path"]
            send_notification(f"Report generated: {summary_path}")

    Args:
        hook_point: Hook point name

    Returns:
        Decorator function

    """

    def decorator(hook_func: Callable) -> Callable:
        HookRegistry.register(hook_point, hook_func)
        return hook_func

    return decorator
