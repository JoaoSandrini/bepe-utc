#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Dict


AVERAGE_PATTERN = re.compile(r"^average\s+(?:delay|rate):\s*([0-9.]+)")
BURST_AVERAGE_PATTERN = re.compile(
	r"^average\s+(?:delay|rate):\s*(?P<average>[0-9.]+)"
)
BURST_DETAILS_PATTERN = re.compile(
	r"^\s*min:\s*(?P<min>[0-9.]+)s\s+max:\s*(?P<max>[0-9.]+)s\s+std dev:\s*(?P<std>[0-9.]+)s\s+window:\s*(?P<window>\d+)"
)
FILE_PATTERN = re.compile(r"^(?P<base>.+)-(?P<idx>\d+)\.txt$")


def extract_values(file_path: Path) -> List[float]:
	values: List[float] = []
	with file_path.open("r", encoding="utf-8") as handle:
		for line in handle:
			match = AVERAGE_PATTERN.match(line.strip())
			if match:
				values.append(float(match.group(1)))
	return values


def extract_burst_records(file_path: Path) -> List[Dict[str, float]]:
	records: List[Dict[str, float]] = []
	current_average: float | None = None
	with file_path.open("r", encoding="utf-8") as handle:
		for line in handle:
			clean = line.strip()
			if not clean or clean.lower() == "no new messages":
				continue
			average_match = BURST_AVERAGE_PATTERN.match(clean)
			if average_match:
				current_average = float(average_match.group("average"))
				continue
			details_match = BURST_DETAILS_PATTERN.match(clean)
			if details_match and current_average is not None:
				records.append(
					{
						"average": current_average,
						"min": float(details_match.group("min")),
						"max": float(details_match.group("max")),
						"std_dev": float(details_match.group("std")),
						"window": int(details_match.group("window")),
					}
				)
				current_average = None
	return records


def group_test_files(folder: Path) -> Dict[str, List[Path]]:
	grouped: Dict[str, List[Path]] = {}
	for file_path in sorted(folder.glob("*.txt")):
		match = FILE_PATTERN.match(file_path.name)
		if not match:
			continue
		base = match.group("base")
		grouped.setdefault(base, []).append(file_path)
	return grouped


def aggregate_values(files: Iterable[Path]) -> List[float]:
	series = [extract_values(path) for path in files]
	series = [values for values in series if values]
	if not series:
		return []
	min_len = min(len(values) for values in series)
	if min_len == 0:
		return []
	return [mean(values[i] for values in series) for i in range(min_len)]


def write_csv(output_path: Path, values: List[float]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(["index", "mean"])
		for idx, value in enumerate(values, start=1):
			writer.writerow([idx, value])


def write_delta_csv(output_path: Path, values: List[float]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(["index", "delta"])
		for idx, value in enumerate(values, start=1):
			writer.writerow([idx, value])


def write_burst_csv(output_path: Path, records: List[Dict[str, float]]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(["index", "average", "min", "max", "std_dev", "window"])
		for idx, record in enumerate(records, start=1):
			writer.writerow(
				[
					idx,
					record["average"],
					record["min"],
					record["max"],
					record["std_dev"],
					record["window"],
				]
			)


def aggregate_folder(input_root: Path, output_root: Path, groups: Iterable[str]) -> None:
	for group in groups:
		group_root = input_root / group
		if not group_root.exists():
			continue
		for folder in group_root.rglob("*"):
			if not folder.is_dir():
				continue
			is_burst = "burst" in folder.parts
			if folder.name not in {"delays", "hz"}:
				continue

			if is_burst:
				burst_root = output_root / "burst" / group
				relative_folder = folder.relative_to(group_root)
				relative_parts = relative_folder.parts
				relative_without_burst = Path(*relative_parts[1:]) if len(relative_parts) > 1 else Path()
				burst_records_by_name: Dict[str, List[Dict[str, float]]] = {}
				for file_path in sorted(folder.glob("*.txt")):
					records = extract_burst_records(file_path)
					if not records:
						print(f"Warning: {file_path} has no burst data.")
						continue
					output_path = (
						burst_root
						/ relative_without_burst
						/ f"{file_path.stem}.csv"
					)
					write_burst_csv(output_path, records)
					burst_records_by_name[file_path.stem] = records

				if folder.name == "delays":
					perceptions = burst_records_by_name.get("perceptions")
					points = burst_records_by_name.get("points")
					if perceptions and points:
						min_len = min(len(perceptions), len(points))
						deltas = [
							perceptions[i]["average"] - points[i]["average"]
							for i in range(min_len)
						]
						delta_path = (
							burst_root
							/ relative_without_burst
							/ "delta.csv"
						)
						write_delta_csv(delta_path, deltas)
				continue

			if not {"off", "on"}.intersection(folder.parts):
				continue

			grouped_files = group_test_files(folder)
			if not grouped_files:
				continue

			aggregated_by_base: Dict[str, List[float]] = {}
			for base, files in grouped_files.items():
				if len(files) != 10:
					print(
						f"Warning: {folder} {base} has {len(files)} files (expected 10)."
					)
				aggregated = aggregate_values(sorted(files))
				if not aggregated:
					print(f"Warning: {folder} {base} has no data.")
					continue

				relative_folder = folder.relative_to(input_root)
				output_path = output_root / relative_folder / f"{base}.csv"
				write_csv(output_path, aggregated)
				aggregated_by_base[base] = aggregated

			if folder.name == "delays":
				perceptions = aggregated_by_base.get("perceptions")
				points = aggregated_by_base.get("points")
				if perceptions and points:
					min_len = min(len(perceptions), len(points))
					deltas = [
						perceptions[i] - points[i] for i in range(min_len)
					]
					relative_folder = folder.relative_to(input_root)
					delta_path = output_root / relative_folder / "delta.csv"
					write_delta_csv(delta_path, deltas)


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "test-results-final"
	default_output = root / "treated-data"
	parser = argparse.ArgumentParser(
		description=(
			"Aggregate delays and hz data by computing the mean across 10 tests."
		)
	)
	parser.add_argument(
		"--input-root",
		type=Path,
		default=default_input,
		help="Root folder containing test-results-final data.",
	)
	parser.add_argument(
		"--output-root",
		type=Path,
		default=default_output,
		help="Folder where aggregated CSVs will be written.",
	)
	parser.add_argument(
		"--groups",
		nargs="+",
		default=["default", "kata", "mixed"],
		help="Top-level groups to aggregate.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	aggregate_folder(args.input_root, args.output_root, args.groups)


if __name__ == "__main__":
	main()
