from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_is_importable() -> None:
    package = importlib.import_module("upi_payment_experiment")
    assert package.__doc__


def test_project_configuration_declares_expected_dependencies() -> None:
    with (ROOT / "pyproject.toml").open("rb") as config_file:
        config = tomllib.load(config_file)

    assert config["project"]["name"] == "upi-payment-experiment"
    assert config["project"]["dependencies"] == [
        "fastapi>=0.115,<1",
        "psycopg[binary]>=3,<4",
        "uvicorn>=0.30,<1",
        "zxing-cpp>=3,<4",
    ]
    assert config["project"]["optional-dependencies"]["test"] == [
        "httpx>=0.27,<1",
        "pytest>=8,<9",
    ]


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
