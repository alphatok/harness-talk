#!/usr/bin/env python3
"""Score a partnership opportunity register using only the Python standard library."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path


WEIGHTS = {
    "customer_access": 15,
    "budget_clarity": 15,
    "problem_value": 15,
    "evidence_strength": 15,
    "capability_fit": 15,
    "acceptance_clarity": 10,
    "commercial_terms": 10,
    "repeatability": 5,
}
REQUIRED_TEXT = ("opportunity_id", "name", "stage", "next_gate")
HARD_GATE_FIELDS = (
    "end_customer",
    "payer",
    "problem",
    "contract_unit",
    "acceptance_metric",
)
ALLOWED_STAGES = {f"H{i}" for i in range(6)}


def parse_score(row: dict[str, str], field: str, row_number: int) -> float:
    raw = (row.get(field) or "").strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"row {row_number}: {field} must be a number from 0 to 5") from exc
    if not 0 <= value <= 5:
        raise ValueError(f"row {row_number}: {field} must be between 0 and 5")
    return value


def score_row(row: dict[str, str], row_number: int) -> dict[str, str]:
    missing = [field for field in REQUIRED_TEXT if not (row.get(field) or "").strip()]
    if missing:
        raise ValueError(f"row {row_number}: missing required values: {', '.join(missing)}")

    stage = row["stage"].strip().upper()
    if stage not in ALLOWED_STAGES:
        raise ValueError(f"row {row_number}: stage must be H0 through H5")

    total = sum(parse_score(row, field, row_number) * weight / 5 for field, weight in WEIGHTS.items())
    gate_gaps = [field for field in HARD_GATE_FIELDS if not (row.get(field) or "").strip()]

    if gate_gaps:
        priority = "verify-first"
    elif total >= 75:
        priority = "A-priority"
    elif total >= 60:
        priority = "B-conditional"
    else:
        priority = "C-observe"

    result = dict(row)
    result["weighted_score"] = f"{total:.1f}"
    result["hard_gate_gaps"] = ";".join(gate_gaps)
    result["recommended_priority"] = priority
    return result


def process(input_stream, output_stream) -> int:
    reader = csv.DictReader(input_stream)
    if not reader.fieldnames:
        raise ValueError("input CSV has no header")
    required_columns = set(REQUIRED_TEXT) | set(HARD_GATE_FIELDS) | set(WEIGHTS)
    missing_columns = sorted(required_columns - set(reader.fieldnames))
    if missing_columns:
        raise ValueError(f"missing columns: {', '.join(missing_columns)}")

    fieldnames = list(reader.fieldnames) + [
        "weighted_score",
        "hard_gate_gaps",
        "recommended_priority",
    ]
    writer = csv.DictWriter(output_stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    count = 0
    for row_number, row in enumerate(reader, start=2):
        writer.writerow(score_row(row, row_number))
        count += 1
    if count == 0:
        raise ValueError("input CSV has no opportunity rows")
    return count


def self_test() -> None:
    columns = list(REQUIRED_TEXT) + list(HARD_GATE_FIELDS) + list(WEIGHTS)
    row = {column: "x" for column in columns}
    row["stage"] = "H2"
    for field in WEIGHTS:
        row[field] = "5"
    source = io.StringIO()
    writer = csv.DictWriter(source, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    source.seek(0)
    target = io.StringIO()
    process(source, target)
    output = target.getvalue()
    if "100.0" not in output or "A-priority" not in output:
        raise AssertionError("unexpected scoring result")

    gated_row = dict(row)
    gated_row["payer"] = ""
    gated_result = score_row(gated_row, 2)
    if gated_result["recommended_priority"] != "verify-first" or "payer" not in gated_result["hard_gate_gaps"]:
        raise AssertionError("hard-gate gap did not override the numerical score")
    print("self-test passed: scoring works and a missing payer forces verify-first")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score and gate partnership opportunities in a CSV register.")
    parser.add_argument("input", nargs="?", type=Path, help="input opportunity register CSV")
    parser.add_argument("-o", "--output", type=Path, help="output scored CSV; defaults to stdout")
    parser.add_argument("--self-test", action="store_true", help="run a built-in deterministic test")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.input is None:
        parser.error("input is required unless --self-test is used")

    try:
        with args.input.open("r", encoding="utf-8-sig", newline="") as input_stream:
            if args.output:
                with args.output.open("w", encoding="utf-8", newline="") as output_stream:
                    count = process(input_stream, output_stream)
            else:
                count = process(input_stream, sys.stdout)
        print(f"scored {count} opportunities", file=sys.stderr)
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
