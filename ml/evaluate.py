from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    report_path = Path("ml/reports/evaluation_report.json")
    if not report_path.exists():
        raise SystemExit("Run `python ml/train.py` before evaluation reporting.")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    print(f"Best model: {report['best_model']}")
    print(f"Test RMSE: {report['test_metrics']['rmse']:.6f}")
    print(f"Test MAE: {report['test_metrics']['mae']:.6f}")
    print(f"Test R2: {report['test_metrics']['r2']:.6f}")


if __name__ == "__main__":
    main()
