"""Every project module imports without errors (no network, dummy env)."""

import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

ROOT_MODULES = [
    "main",
    "ai_framework",
    "messagebus",
    "rate_limiter",
    "telemetry",
    "base",
    "offline_cache",
    "token_haze",
    "pantheon_rlm",
    "pantheon_swarm",
    "startup",
    "web_dashboard",
]


# Modules that need packages not listed in requirements.txt. They are skipped
# (not failed) when the package is missing.
OPTIONAL_DEPS = {
    "src.mcp_servers.data_science": ["pandas", "numpy"],
}


def _src_modules():
    names = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        rel = path.relative_to(ROOT).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        names.append(".".join(parts))
    return names


@pytest.mark.parametrize("name", ROOT_MODULES)
def test_root_module_imports(name):
    assert importlib.import_module(name) is not None


@pytest.mark.parametrize("name", _src_modules())
def test_src_module_imports(name):
    for dep in OPTIONAL_DEPS.get(name, []):
        pytest.importorskip(dep)
    assert importlib.import_module(name) is not None
