#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


RUNTIME_COLOR_MAP = {
	"default": "#1f77b4",
	"kata": "#ff7f0e",
}


def read_delta_series(csv_path: Path) -> Tuple[List[int], List[float]]:
	indices: List[int] = []
	values: List[float] = []
	with csv_path.open("r", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		for row in reader:
			indices.append(int(row["index"]))
			values.append(float(row["delta"]))
	return indices, values


def collect_burst_series(input_root: Path, groups: List[str]) -> Dict[str, Tuple[List[int], List[float]]]:
	series: Dict[str, Tuple[List[int], List[float]]] = {}
	for group in groups:
		path = input_root / group / "delays" / "delta.csv"
		if not path.exists():
			continue
		series[group] = read_delta_series(path)
	return series


def plot_burst_deltas(series: Dict[str, Tuple[List[int], List[float]]], output_dir: Path) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)
	if not series:
		return
	fig, ax = plt.subplots(figsize=(10, 6))
	for group, (xs, ys) in series.items():
		ax.plot(
			xs,
			ys,
			label=f"{group.capitalize()} Runtime",
			linewidth=1.8,
			color=RUNTIME_COLOR_MAP.get(group, "#333333"),
		)
	ax.set_xlabel("Measurement Index")
	ax.set_ylabel("Processing Time (s)")
	ax.set_title("Topic Delay Delta - Burst")
	ax.grid(True, alpha=0.3)
	ax.legend(loc="center right")
	fig.tight_layout()
	fig.savefig(output_dir / "burst-delta.png", dpi=150)
	plt.close(fig)


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data" / "burst"
	default_output = root / "plots" / "burst"
	parser = argparse.ArgumentParser(description="Plot burst delta series for all runtimes.")
	parser.add_argument(
		"--input-root",
		type=Path,
		default=default_input,
		help="Root folder containing burst treated-data.",
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
	series = collect_burst_series(args.input_root, args.groups)
	if not series:
		raise SystemExit("No burst delta.csv files found to plot.")
	plot_burst_deltas(series, args.output_dir)


if __name__ == "__main__":
	main()
