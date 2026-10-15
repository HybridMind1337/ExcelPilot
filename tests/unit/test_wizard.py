"""Unit tests for the interactive wizard controller."""

from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from excelpilot.cli.exit_codes import ExitCode
from excelpilot.cli.wizard import WizardController


def test_wizard_run_nonexistent_file(tmp_path: Path) -> None:
    controller = WizardController(console=Console(record=True))
    code = controller.run(tmp_path / "does_not_exist.xlsx")
    assert code == ExitCode.WORKBOOK_ERROR


def test_wizard_full_flow(sales_workbook_path: Path, tmp_path: Path) -> None:
    controller = WizardController(console=Console(record=True))
    target_out = tmp_path / "wizard_out.xlsx"

    # Simulate user answers: purpose="1" (Sales), metric="1" (Revenue), confirm=True
    with (
        patch("rich.prompt.Prompt.ask", side_effect=["1", "1"]),
        patch("rich.prompt.Confirm.ask", return_value=True),
    ):
        code = controller.run(workbook_path=sales_workbook_path, output_path=target_out)

    assert code == ExitCode.SUCCESS
    assert target_out.exists()
    assert target_out.stat().st_size > 0
