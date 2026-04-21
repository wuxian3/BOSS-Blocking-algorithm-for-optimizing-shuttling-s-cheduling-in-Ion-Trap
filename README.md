# TILT Simulation Ver3

This directory is a release-oriented version of the TILT simulation project.
Source code of https://arxiv.org/pdf/2412.03443

## Overview

`ver3` provides a simplified command-line entry for running a single simulation on one QASM file.

The default workflow uses:

- application mode: `QASM`
- default QASM file: `qasm_file/ALT64.qasm`
- default block size: `16`
- default qubit number: `64`
- default gate model: `Trout`

## Directory Notes

- `run.py`: recommended command-line entry
- `run.sh`: sample launch script
- `TILT_main.py`: primary implementation entry used by `run.py`
- `TILT_main2.py`: alternate single-file test entry
- `qasm_file/`: bundled QASM inputs for release

Only the following QASM files are intentionally retained in this version:

- `qasm_file/ALT64.qasm`
- `qasm_file/test.qasm`

## Requirements

Run this project with Python from PowerShell or another shell environment.

Some project dependencies are required at runtime. Based on the current codebase, the main execution path imports modules that may require packages such as:

- `qiskit`
- `torch`

If these packages are missing, the CLI can still show `--help`, but simulation execution will fail until the environment is prepared.

## Quick Start

From the project root:

```powershell
cd "D:\Quantum Computing\Ion Trap\TILT simulation (ver2)"
python .\ver3\run.py --qasm .\ver3\qasm_file\ALT64.qasm --block-size 16 --qb-num 64
```

Or enter the release directory first:

```powershell
cd "D:\Quantum Computing\Ion Trap\TILT simulation (ver2)\ver3"
python .\run.py --qasm .\qasm_file\ALT64.qasm --block-size 16 --qb-num 64
```

## CLI Usage

Show help:

```powershell
python .\ver3\run.py --help
```

Available arguments:

- `--qasm`: path to a QASM file
- `--qb-num`: number of qubits
- `--block-size`: execution block size
- `--gate-model`: one of `Duan`, `Trout`, `PM`
- `--application`: one of `QASM`
- `--print-layout`: print intermediate tape layout output
- `--json`: print results in JSON format

## Example Commands

Default release input:

```powershell
python .\ver3\run.py --qasm .\ver3\qasm_file\ALT64.qasm --block-size 16 --qb-num 64
```

Use JSON output:

```powershell
python .\ver3\run.py --qasm .\ver3\qasm_file\ALT64.qasm --block-size 16 --qb-num 64 --json
```

Use the alternate retained QASM file:

```powershell
python .\ver3\run.py --qasm .\ver3\qasm_file\test.qasm --block-size 16 --qb-num 64
```

## Output Fields

The CLI prints the following result fields:

- `application`
- `qasm_file`
- `qb_num`
- `block_size`
- `gate_model`
- `shuttles`
- `shuttle_dis`
- `swap_cnt`
- `compilation_time`
- `execution_time`
- `success_rate`
- `gate_distance`

## Notes

- This release version removes the previously retained WXC-related execution path from the main entry files.
- The default release path is intended for single-file command-line execution instead of parameter sweeps over multiple qubit counts.
- `run.sh` is included as a convenience sample and preserves the PowerShell-style example command in comments.
