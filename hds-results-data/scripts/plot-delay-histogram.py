#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt


COLOR_MAP = {
	"default_off": "#1f77b4",
	"default_on": "#1f77b4",
	"kata_off": "#ff7f0e",
	"kata_on": "#ff7f0e",
}


def read_delta_values(csv_path: Path) -> List[float]:
	values: List[float] = []
	with csv_path.open("r", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		for row in reader:
			values.append(float(row["delta"]))
	return values


def collect_delta_series(input_root: Path, groups: List[str]) -> Dict[str, Dict[str, List[float]]]:
	collected: Dict[str, Dict[str, List[float]]] = {}
	for group in groups:
		group_root = input_root / group
		for state in ["off", "on"]:
			path = group_root / state / "delays" / "delta.csv"
			if not path.exists():
				continue
			collected.setdefault(group, {})[state] = read_delta_values(path)
	return collected


def plot_histogram_by_load(collected: Dict[str, Dict[str, List[float]]], output_dir: Path, state: str) -> None:
	plt.figure(figsize=(10, 6))
	plotted = False
	for group, group_series in collected.items():
		values = group_series.get(state, [])
		if not values:
			continue
		plotted = True
		plt.hist(
			values,
			bins=30,
			density=True,
			alpha=0.7,
			label=f"{group.capitalize()} Runtime",
			color=COLOR_MAP.get(f"{group}_{state}"),
		)
	if not plotted:
		plt.close()
		return
	plt.xlabel("Processing Time (s)")
	plt.ylabel("Density")
	plt.title(f"Topic Delay Delta Frequency Distribution - Competing Load {state.capitalize()}")
	plt.grid(True, alpha=0.3)
	plt.legend(loc="upper right")
	plt.tight_layout()
	plt.savefig(output_dir / f"histogram-{state}.png", dpi=150)
	plt.close()


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data"
	default_output = root / "plots" / "delay-delta" / "histogram"
	parser = argparse.ArgumentParser(
		description="Plot histograms of delta values organized like index plots."
	)
	parser.add_argument(
		"--input-root",
		type=Path,
		default=default_input,
		help="Root folder containing treated-data.",
	)
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=default_output,
		help="Folder where plots will be written.",
	)
	parser.add_argument(
		"--groups",
		nargs="+",
		default=["default", "kata"],
		help="Groups to plot.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	output_dir = args.output_dir
	output_dir.mkdir(parents=True, exist_ok=True)
	collected = collect_delta_series(args.input_root, args.groups)
	plot_histogram_by_load(collected, output_dir, "on")
	plot_histogram_by_load(collected, output_dir, "off")


if __name__ == "__main__":
	main()
