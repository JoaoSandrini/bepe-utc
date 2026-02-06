#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


COLOR_MAP = {
	"default_off": "#1f77b4",
	"default_on": "#ff7f0e",
	"kata_off": "#2ecc71",
	"kata_on": "#d62728",
}

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




def collect_delta_series(
	input_root: Path,
	groups: List[str],
) -> Dict[str, Dict[str, Tuple[List[int], List[float]]]]:
	collected: Dict[str, Dict[str, Tuple[List[int], List[float]]]] = {}
	for group in groups:
		group_root = input_root / group
		off_path = group_root / "off" / "delays" / "delta.csv"
		on_path = group_root / "on" / "delays" / "delta.csv"
		group_series: Dict[str, Tuple[List[int], List[float]]] = {}
		if off_path.exists():
			group_series["off"] = read_delta_series(off_path)
		if on_path.exists():
			group_series["on"] = read_delta_series(on_path)
		if group_series:
			collected[group] = group_series
	return collected


def compute_global_limits(
	collected: Dict[str, Dict[str, Tuple[List[int], List[float]]]],
) -> Tuple[float, float]:
	values: List[float] = []
	for group_series in collected.values():
		for _, (_, ys) in group_series.items():
			values.extend(ys)
	if not values:
		return 0.0, 1.0
	min_value = min(values)
	max_value = max(values)
	if min_value == max_value:
		return min_value - 1.0, max_value + 1.0
	padding = (max_value - min_value) * 0.05
	return min_value - padding, max_value + padding




def plot_delta_off_on(
	input_root: Path,
	output_root: Path,
	group: str,
	y_limits: Tuple[float, float],
) -> None:
	group_root = input_root / group
	off_root = group_root / "off" / "delays"
	on_root = group_root / "on" / "delays"
	output_dir = output_root
	output_dir.mkdir(parents=True, exist_ok=True)

	off_path = off_root / "delta.csv"
	on_path = on_root / "delta.csv"
	if not off_path.exists() or not on_path.exists():
		return

	off_x, off_y = read_delta_series(off_path)
	on_x, on_y = read_delta_series(on_path)

	plt.figure(figsize=(10, 6))
	plt.plot(
		off_x,
		off_y,
		label="Load Off",
		linewidth=1.8,
		color="#1f77b4",
	)
	plt.plot(
		on_x,
		on_y,
		label="Load On",
		linewidth=1.8,
		color="#ff7f0e",
	)
	plt.ylim(*y_limits)
	plt.xlabel("Measurement Index")
	plt.ylabel("Processing Time (s)")
	plt.title(f" Topic Delay Delta - {group.capitalize()} Runtime")
	plt.grid(True, alpha=0.3)
	plt.legend(loc="center right")
	plt.tight_layout()
	plt.savefig(output_dir / f"index-{group}.png", dpi=150)
	plt.close()


def plot_delta_all(
	collected: Dict[str, Dict[str, Tuple[List[int], List[float]]]],
	output_root: Path,
	y_limits: Tuple[float, float],
) -> None:
	output_dir = output_root
	output_dir.mkdir(parents=True, exist_ok=True)

	if not collected:
		return

	plt.figure(figsize=(10, 6))
	for group, group_series in collected.items():
		for state, (xs, ys) in group_series.items():
			plt.plot(
				xs,
				ys,
				label=f"{group.capitalize()} Runtime - Load {state.capitalize()}",
				linewidth=1.8,
				color=COLOR_MAP.get(f"{group}_{state}"),
			)
	plt.ylim(*y_limits)
	plt.xlabel("Measurement Index")
	plt.ylabel("Processing Time (s)")
	plt.title("Topic Delay Delta (/perceptions - /points)")
	plt.grid(True, alpha=0.3)
	plt.legend(loc="center right")
	plt.tight_layout()
	plt.savefig(output_dir / "index-all.png", dpi=150)
	plt.close()


def plot_delta_by_load(
	collected: Dict[str, Dict[str, Tuple[List[int], List[float]]]],
	output_root: Path,
	y_limits: Tuple[float, float],
	state: str,
) -> None:
	output_dir = output_root
	output_dir.mkdir(parents=True, exist_ok=True)

	series_by_group: Dict[str, Tuple[List[int], List[float]]] = {}
	for group, group_series in collected.items():
		if state in group_series:
			series_by_group[group] = group_series[state]

	if not series_by_group:
		return

	plt.figure(figsize=(10, 6))
	for group, (xs, ys) in series_by_group.items():
		plt.plot(
			xs,
			ys,
			label=f"{group.capitalize()} Runtime",
			linewidth=1.8,
			color=RUNTIME_COLOR_MAP.get(group, "#333333"),
		)
	plt.ylim(*y_limits)
	plt.xlabel("Measurement Index")
	plt.ylabel("Processing Time (s)")
	plt.title(f"Topic Delay Delta - Competing Load {state.capitalize()}")
	plt.grid(True, alpha=0.3)
	plt.legend(loc="center right")
	plt.tight_layout()
	plt.savefig(output_dir / f"index-{state}.png", dpi=150)
	plt.close()




def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data"
	default_output = root / "plots" / "delay-delta" / "index"
	parser = argparse.ArgumentParser(
		description="Plot delta (perceptions - points) per index for off/on and burst runs."
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
	collected = collect_delta_series(args.input_root, args.groups)
	y_limits = compute_global_limits(collected)
	for group in args.groups:
		plot_delta_off_on(args.input_root, args.output_dir, group, y_limits)
	plot_delta_all(collected, args.output_dir, y_limits)
	plot_delta_by_load(collected, args.output_dir, y_limits, "on")
	plot_delta_by_load(collected, args.output_dir, y_limits, "off")


if __name__ == "__main__":
	main()
