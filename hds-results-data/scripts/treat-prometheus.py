#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from statistics import mean
from typing import Dict, List, Sequence, Tuple


START_PATTERN = re.compile(r"Starting .*? timestamp (?P<ts>\d+)")
END_PATTERN = re.compile(r"Ending .*? timestamp (?P<ts>\d+)")


def parse_timestamps(timestamps_path: Path) -> List[Tuple[int, int]]:
	lines = [line.strip() for line in timestamps_path.read_text(encoding="utf-8").splitlines()]
	lines = [line for line in lines if line]
	if not lines:
		return []

	if all(line.isdigit() for line in lines):
		numbers = [int(line) for line in lines]
		pairs: List[Tuple[int, int]] = []
		for i in range(0, len(numbers) - 1, 2):
			pairs.append((numbers[i], numbers[i + 1]))
		return pairs

	starts: List[int] = []
	ends: List[int] = []
	for line in lines:
		start_match = START_PATTERN.search(line)
		if start_match:
			starts.append(int(start_match.group("ts")))
			continue
		end_match = END_PATTERN.search(line)
		if end_match:
			ends.append(int(end_match.group("ts")))

	pairs = []
	for start, end in zip(starts, ends):
		pairs.append((start, end))
	return pairs


def parse_prometheus_json(json_path: Path) -> List[Tuple[int, float]]:
	content = json.loads(json_path.read_text(encoding="utf-8"))
	results = content.get("data", {}).get("result", [])
	if not results:
		return []

	values_by_timestamp: Dict[int, List[float]] = {}
	for result in results:
		for timestamp, value in result.get("values", []):
			ts = int(float(timestamp))
			values_by_timestamp.setdefault(ts, []).append(float(value))

	series: List[Tuple[int, float]] = []
	for ts in sorted(values_by_timestamp.keys()):
		series.append((ts, mean(values_by_timestamp[ts])))
	return series


def split_series_by_runs(
	series: Sequence[Tuple[int, float]],
	runs: Sequence[Tuple[int, int]],
) -> List[List[Tuple[int, float]]]:
	split: List[List[Tuple[int, float]]] = []
	if not series or not runs:
		return split

	for index, (start, end) in enumerate(runs):
		is_last = index == len(runs) - 1
		if is_last:
			chunk = [(ts, value) for ts, value in series if start <= ts <= end]
		else:
			chunk = [(ts, value) for ts, value in series if start <= ts < end]
		split.append(chunk)
	return split


def aggregate_runs(run_series: Sequence[Sequence[Tuple[int, float]]]) -> List[float]:
	series_values = [[value for _, value in series] for series in run_series if series]
	if not series_values:
		return []
	min_len = min(len(values) for values in series_values)
	if min_len == 0:
		return []
	return [mean(values[i] for values in series_values) for i in range(min_len)]


def write_run_csv(output_path: Path, series: Sequence[Tuple[int, float]], start_ts: int) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(["index", "timestamp", "relative_time", "value"])
		for idx, (ts, value) in enumerate(series, start=1):
			writer.writerow([idx, ts, ts - start_ts, value])


def write_aggregate_csv(output_path: Path, values: Sequence[float]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(["index", "mean"])
		for idx, value in enumerate(values, start=1):
			writer.writerow([idx, value])


def build_output_root(
	input_root: Path,
	output_root: Path,
	group_root: Path,
	prometheus_folder: Path,
) -> Path:
	relative = prometheus_folder.relative_to(group_root)
	if "burst" in prometheus_folder.parts:
		relative_parts = relative.parts
		relative_without_burst = Path(*relative_parts[1:]) if relative_parts else Path()
		return output_root / "burst" / group_root.name / relative_without_burst
	return output_root / group_root.name / relative


def treat_prometheus_group(input_root: Path, output_root: Path, group: str) -> None:
	group_root = input_root / group
	if not group_root.exists():
		return

	for prometheus_folder in group_root.rglob("prometheus"):
		if not prometheus_folder.is_dir():
			continue

		timestamps_path = prometheus_folder.parent / "timestamps" / "timestamps.txt"
		if not timestamps_path.exists():
			print(f"Warning: Missing timestamps for {prometheus_folder}")
			continue

		runs = parse_timestamps(timestamps_path)
		if not runs:
			print(f"Warning: No timestamps parsed for {timestamps_path}")
			continue

		output_prometheus_root = build_output_root(
			input_root=input_root,
			output_root=output_root,
			group_root=group_root,
			prometheus_folder=prometheus_folder,
		)

		for json_path in sorted(prometheus_folder.glob("*.json")):
			series = parse_prometheus_json(json_path)
			if not series:
				print(f"Warning: No series data in {json_path}")
				continue

			run_series = split_series_by_runs(series, runs)
			metric_root = output_prometheus_root / json_path.stem
			for index, (run, (start_ts, _)) in enumerate(zip(run_series, runs), start=1):
				if not run:
					print(f"Warning: Empty run {index} for {json_path}")
					continue
				write_run_csv(metric_root / f"run-{index}.csv", run, start_ts)

			aggregated = aggregate_runs(run_series)
			if not aggregated:
				print(f"Warning: No aggregated data for {json_path}")
				continue
			write_aggregate_csv(metric_root / "mean.csv", aggregated)


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "test-results-final"
	default_output = root / "treated-data"
	parser = argparse.ArgumentParser(
		description="Parse Prometheus JSONs, split per run using timestamps, and aggregate."
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
		help="Folder where treated CSVs will be written.",
	)
	parser.add_argument(
		"--groups",
		nargs="+",
		default=["default", "kata", "mixed"],
		help="Top-level groups to process.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	for group in args.groups:
		treat_prometheus_group(args.input_root, args.output_root, group)


if __name__ == "__main__":
	main()
