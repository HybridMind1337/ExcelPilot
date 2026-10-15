"""Unit tests for configuration loading and validation."""

from pathlib import Path

import pytest

from excelpilot.config.loader import ConfigLoader
from excelpilot.exceptions.base import ConfigurationError


def test_create_and_load_example_config(tmp_path: Path) -> None:
    config_file = tmp_path / "excelpilot.yaml"
    ConfigLoader.create_example_config(config_file)
    assert config_file.exists()

    cfg = ConfigLoader.load(config_file)
    assert cfg.project.name == "northstar-retail"
    assert "total_revenue" in cfg.metrics
    assert cfg.metrics["total_revenue"].column == "Revenue"
    assert "Region" in cfg.dimensions


def test_load_invalid_yaml(tmp_path: Path) -> None:
    bad_file = tmp_path / "invalid.yaml"
    bad_file.write_text("project: [unclosed list", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="YAML parsing error"):
        ConfigLoader.load(bad_file)


def test_load_schema_violation(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad_schema.yaml"
    bad_file.write_text(
        """
        metrics:
          rev:
            aggregation: invalid_agg_type
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="validation failed"):
        ConfigLoader.load(bad_file)
