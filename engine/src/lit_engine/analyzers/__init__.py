"""Base analyzer interface and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AnalyzerResult:
    """Standard wrapper for analyzer output."""

    analyzer_name: str
    data: dict  # JSON-serializable payload
    warnings: list[str] = field(default_factory=list)


class Analyzer(ABC):
    """Base interface for all analyzers."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        """
        Accept raw text + config, return structured result.

        Args:
            text: Raw manuscript text (BOM-stripped, ready to process).
            config: Merged configuration dict (see config.py).
            context: Results from previously-run analyzers, keyed by
                     analyzer name. None for analyzers with no dependencies.
                     Example: {"texttiling": <AnalyzerResult>, ...}

        Returns:
            AnalyzerResult with JSON-serializable `data` dict.
        """
        ...

    def requires(self) -> list[str]:
        """List analyzer names this depends on (for execution ordering)."""
        return []


# Analyzer registry — populated by each analyzer module on import
_REGISTRY: dict[str, type[Analyzer]] = {}


def register(cls: type[Analyzer]) -> type[Analyzer]:
    """Decorator to register an analyzer class."""
    _REGISTRY[cls.name] = cls
    return cls


def get_analyzer(name: str) -> Analyzer:
    """Instantiate a registered analyzer by name."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown analyzer: {name!r}. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]()


def list_analyzers() -> list[str]:
    """Return names of all registered analyzers."""
    return sorted(_REGISTRY.keys())


def resolve_execution_order(analyzer_names: list[str]) -> list[str]:
    """
    Topological sort of analyzer names using requires().

    Uses Kahn's algorithm.

    Raises ValueError if:
    - A required dependency is not in the requested set (fail-fast).
    - A circular dependency is detected.

    Returns analyzer_names reordered so dependencies come before dependents.
    """
    name_set = set(analyzer_names)

    # Validate all dependencies are in the requested set
    for name in analyzer_names:
        if name not in _REGISTRY:
            continue  # unknown analyzers handled elsewhere
        analyzer = _REGISTRY[name]()
        for dep in analyzer.requires():
            if dep not in name_set:
                raise ValueError(
                    f"Analyzer {name!r} requires {dep!r} which is not in "
                    f"the requested set: {sorted(name_set)}"
                )

    # Build adjacency: dep → set of dependents
    in_degree: dict[str, int] = {name: 0 for name in analyzer_names}
    dependents: dict[str, list[str]] = {name: [] for name in analyzer_names}

    for name in analyzer_names:
        if name not in _REGISTRY:
            continue
        analyzer = _REGISTRY[name]()
        for dep in analyzer.requires():
            if dep in name_set:
                in_degree[name] += 1
                dependents[dep].append(name)

    # Kahn's algorithm
    queue = sorted(n for n in analyzer_names if in_degree[n] == 0)
    result: list[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for dependent in sorted(dependents.get(node, [])):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(analyzer_names):
        remaining = set(analyzer_names) - set(result)
        raise ValueError(f"Circular dependency detected among: {sorted(remaining)}")

    return result


# Import analyzer modules so their @register decorators execute.
# Each new analyzer module added in later stages gets a line here.
from lit_engine.analyzers import texttiling  # noqa: F401, E402
from lit_engine.analyzers import agency  # noqa: F401, E402
from lit_engine.analyzers import dialogue  # noqa: F401, E402
from lit_engine.analyzers import readability  # noqa: F401, E402
from lit_engine.analyzers import pacing  # noqa: F401, E402
from lit_engine.analyzers import sentiment  # noqa: F401, E402
from lit_engine.analyzers import silence  # noqa: F401, E402
from lit_engine.analyzers import chapters  # noqa: F401, E402
