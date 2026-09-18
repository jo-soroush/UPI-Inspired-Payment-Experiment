from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_is_importable() -> None:
    package = importlib.import_module("upi_payment_experiment")
    assert package.__doc__


def test_project_configuration_declares_only_c01_test_dependency() -> None:
    with (ROOT / "pyproject.toml").open("rb") as config_file:
        config = tomllib.load(config_file)

    assert config["project"]["name"] == "upi-payment-experiment"
    assert config["project"]["dependencies"] == []
    assert "pytest" in config["project"]["optional-dependencies"]["test"][0]


def test_canonical_documents_remain_at_repository_root() -> None:
    canonical_documents = (
        "AGENTS.md",
        "PROJECT_CONTROL.md",
        "README.md",
        "UPI_PAYMENT_INTERVIEW_ROADMAP.md",
        "PAYMENT_CARD_EVIDENCE_MAP.md",
        "ARCHITECTURE_AND_DECISIONS.md",
        "BENCHMARK_AND_EXPERIMENT_PLAN.md",
        ".gitignore",
    )

    assert all((ROOT / document).is_file() for document in canonical_documents)
