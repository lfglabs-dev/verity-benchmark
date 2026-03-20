#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from toml_compat import load_toml_file

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_TOML = ROOT / "benchmark.toml"

DEFAULT_AGENT_PROFILES_DIR = Path("harness/agents")
DEFAULT_AGENT_DEFAULT_PROFILE = "default"
CUSTOM_AGENT_DEFAULT_PROFILE = "openai-compatible"
DEFAULT_AGENT_CONFIG = Path("harness/agents/default.json")


@dataclass(frozen=True)
class BenchmarkAgentDefaults:
    default_agent_profiles_dir: Path
    default_agent_default_profile: str
    custom_agent_default_profile: str
    default_agent_config: Path


def _string_setting(raw: object, fallback: str) -> str:
    if isinstance(raw, str):
        value = raw.strip()
        if value:
            return value
    return fallback


def _path_setting(raw: object, fallback: Path) -> Path:
    return Path(_string_setting(raw, str(fallback)))


@lru_cache(maxsize=1)
def load_benchmark_agent_defaults() -> BenchmarkAgentDefaults:
    data: dict[str, object] = {}
    if BENCHMARK_TOML.is_file():
        data = load_toml_file(BENCHMARK_TOML)
    return BenchmarkAgentDefaults(
        default_agent_profiles_dir=_path_setting(data.get("default_agent_profiles_dir"), DEFAULT_AGENT_PROFILES_DIR),
        default_agent_default_profile=_string_setting(
            data.get("default_agent_default_profile"),
            DEFAULT_AGENT_DEFAULT_PROFILE,
        ),
        custom_agent_default_profile=_string_setting(
            data.get("custom_agent_default_profile"),
            CUSTOM_AGENT_DEFAULT_PROFILE,
        ),
        default_agent_config=_path_setting(data.get("default_agent_config"), DEFAULT_AGENT_CONFIG),
    )
