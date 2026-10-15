"""Configuration loading and validation."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from excelpilot.config.models import ExcelPilotConfig
from excelpilot.exceptions.base import ConfigurationError


class ConfigLoader:
    """Loads and validates project configuration files."""

    @staticmethod
    def load(path: Path) -> ExcelPilotConfig:
        """Load and validate an excelpilot.yaml configuration file."""
        if not path.exists():
            raise ConfigurationError(f"Configuration file does not exist at '{path}'.")
        if not path.is_file():
            raise ConfigurationError(f"Configuration path '{path}' is not a valid file.")

        try:
            content = path.read_text(encoding="utf-8")
            raw_data = yaml.safe_load(content)
        except yaml.YAMLError as err:
            raise ConfigurationError(f"YAML parsing error in '{path}': {err}") from err
        except Exception as err:
            raise ConfigurationError(f"Failed to read configuration file '{path}': {err}") from err

        if not isinstance(raw_data, dict):
            raise ConfigurationError(
                f"Configuration file '{path}' must contain a YAML mapping (dictionary)."
            )

        try:
            return ExcelPilotConfig.model_validate(raw_data)
        except ValidationError as err:
            # Produce clean, specific error messages
            error_msgs: list[str] = []
            for issue in err.errors():
                loc = " -> ".join(str(elem) for elem in issue["loc"])
                msg = issue["msg"]
                error_msgs.append(f"Field '{loc}': {msg}")
            details = "\n  ".join(error_msgs)
            raise ConfigurationError(
                f"Configuration schema validation failed for '{path}':\n  {details}"
            ) from err

    @staticmethod
    def create_example_config(target_path: Path) -> Path:
        """Generate a commented starter excelpilot.yaml file."""
        example_yaml = """# ExcelPilot Project Configuration
project:
  name: northstar-retail
  version: "1.0"

source:
  worksheet: Sales

metrics:
  total_revenue:
    label: Total Revenue
    column: Revenue
    aggregation: sum
    format_type: currency

  total_orders:
    label: Total Transactions
    column: OrderID
    aggregation: count_distinct
    format_type: integer

  profit_margin:
    label: Profit Margin
    formula: (Revenue - Cost) / Revenue * 100
    format_type: percentage

dimensions:
  - Region
  - Channel
  - Category

time:
  column: OrderDate
  granularity: month

dashboard:
  title: Retail Performance Dashboard
  theme: executive
  currency: GBP

quality:
  Revenue:
    nullable: false
    minimum: 0.0

output:
  path: reports/retail-dashboard.xlsx
"""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(example_yaml, encoding="utf-8")
        return target_path.resolve()
