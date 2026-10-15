"""Generate synthetic retail sales workbook for demonstration and evaluation."""

import sys
from pathlib import Path

# Ensure project source is accessible
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.fixtures.synthetic_workbooks import create_synthetic_sales_workbook


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    target = data_dir / "sales.xlsx"
    create_synthetic_sales_workbook(target)
    print(f"Generated sample sales workbook at: {target.resolve()}")


if __name__ == "__main__":
    main()
