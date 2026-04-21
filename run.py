from __future__ import annotations

import argparse
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def resolve_qasm_path(qasm: str) -> str:
    raw_path = Path(qasm)
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append(raw_path)
        candidates.append(BASE_DIR / raw_path)
        candidates.append(BASE_DIR / "qasm_file" / raw_path.name)
    for candidate in candidates:
        if candidate.exists():
            try:
                return str(candidate.relative_to(BASE_DIR)).replace("\\", "/")
            except ValueError:
                return str(candidate)
    raise FileNotFoundError(f"QASM file not found: {qasm}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a single TILT simulation from the command line."
    )
    parser.add_argument(
        "--qasm",
        default="qasm_file/ALT64.qasm",
        help="Path to the QASM file. Defaults to qasm_file/ALT64.qasm.",
    )
    parser.add_argument(
        "--qb-num",
        type=int,
        default=64,
        help="Number of qubits to use.",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=16,
        help="Execution block size.",
    )
    parser.add_argument(
        "--gate-model",
        default="Trout",
        choices=["Duan", "Trout", "PM"],
        help="Gate timing model.",
    )
    parser.add_argument(
        "--application",
        default="QASM",
        choices=["QASM"],
        help="Application mode. (other mode not supported yet)",
    )
    parser.add_argument(
        "--print-layout",
        action="store_true",
        help="Print the tape layout during scheduling.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON.",
    )
    return parser


def format_result(application: str, qasm_file: str, qb_num: int, block_size: int, gate_model: str, result: list[float]) -> dict[str, object]:
    return {
        "application": application,
        "qasm_file": qasm_file,
        "qb_num": qb_num,
        "block_size": block_size,
        "gate_model": gate_model,
        "shuttles": result[0],
        "shuttle_dis": result[1],
        "swap_cnt": result[2],
        "compilation_time": result[3],
        "execution_time": result[4],
        "success_rate": result[5],
        "gate_distance": result[6],
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    from TILT_main import TILT_main

    qasm_file = resolve_qasm_path(args.qasm)
    result = TILT_main(
        Application=args.application,
        qb_num=args.qb_num,
        block_size=args.block_size,
        gate_model=args.gate_model,
        QASM_FILE=qasm_file,
        print_flag=args.print_layout,
    )
    payload = format_result(
        application=args.application,
        qasm_file=qasm_file,
        qb_num=args.qb_num,
        block_size=args.block_size,
        gate_model=args.gate_model,
        result=result,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    for key, value in payload.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
