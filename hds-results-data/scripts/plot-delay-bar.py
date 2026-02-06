#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


COLOR_MAP = {
	"default": "#1f77b4",
	"kata": "#ff7f0e",
	"off": "#1f77b4",
	"on": "#ff7f0e",
}


def read_delta_values(csv_path: Path) -> List[float]:
	values: List[float] = []
	with csv_path.open("r", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		for row in reader:
			values.append(float(row["delta"]))
	return values


def collect_delta_means(input_root: Path, groups: List[str]) -> Dict[str, Dict[str, float]]:
	means: Dict[str, Dict[str, float]] = {}
	for group in groups:
		group_root = input_root / group
		for state in ["off", "on"]:
			path = group_root / state / "delays" / "delta.csv"
			if not path.exists():
				continue
			values = read_delta_values(path)
			if not values:
				continue
			means.setdefault(group, {})[state] = mean(values)
	return means


def plot_bar_by_load(
	means: Dict[str, Dict[str, float]],
	output_dir: Path,
) -> None:
	order: List[Tuple[str, str]] = [("default", "off"), ("kata", "off"), ("default", "on"), ("kata", "on")]
	labels = ["Off", "Off", "On", "On"]
	values: List[Optional[float]] = []
	colors: List[str] = []
	for group, state in order:
		value = means.get(group, {}).get(state)
		values.append(value)
		colors.append(COLOR_MAP.get(group, "#999999"))

	positions = list(range(1, len(order) + 1))
	fig, ax = plt.subplots(figsize=(10, 6))
	bars = ax.bar(positions, values, color=colors, alpha=0.85, edgecolor="#000000")
	plt.xticks(positions, labels)
	plt.xlabel("Competing Load")
	plt.ylabel("Mean Processing Time (s)")
	plt.title("Mean Topic Delay Delta by Load State")
	plt.grid(True, axis="y", alpha=0.3)
	for bar, value in zip(bars, values, strict=False):
		if value is None:
			continue
		height = bar.get_height()
		ax.text(
			bar.get_x() + bar.get_width() / 2,
			height,
			f"{value:.3f}",
			ha="center",
			va="bottom",
			fontsize=12,
			fontweight="bold"
		)
	legend_handles = [
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=COLOR_MAP["default"], markersize=10),
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=COLOR_MAP["kata"], markersize=10),
	]
	plt.legend(legend_handles, ["Default Runtime", "Kata Runtime"], loc="center right")
	plt.tight_layout()
	plt.savefig(output_dir / "bar-load.png", dpi=150)
	plt.close()


def plot_bar_by_runtime(
	means: Dict[str, Dict[str, float]],
	output_dir: Path,
) -> None:
	order: List[Tuple[str, str]] = [("default", "off"), ("default", "on"), ("kata", "off"), ("kata", "on")]
	labels = ["Default", "Default", "Kata", "Kata"]
	values: List[Optional[float]] = []
	colors: List[str] = []
	for group, state in order:
		value = means.get(group, {}).get(state)
		values.append(value)
		colors.append(COLOR_MAP.get(state, "#999999"))

	positions = list(range(1, len(order) + 1))
	fig, ax = plt.subplots(figsize=(10, 6))
	bars = ax.bar(positions, values, color=colors, alpha=0.85, edgecolor="#000000")
	plt.xticks(positions, labels)
	plt.xlabel("Runtime")
	plt.ylabel("Mean Processing Time (s)")
	plt.title("Mean Topic Delay Delta by Runtime")
	plt.grid(True, axis="y", alpha=0.3)
	for bar, value in zip(bars, values, strict=False):
		if value is None:
			continue
		height = bar.get_height()
		ax.text(
			bar.get_x() + bar.get_width() / 2,
			height,
			f"{value:.3f}",
			ha="center",
			va="bottom",
			fontsize=12,
			fontweight="bold"
		)
	legend_handles = [
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=COLOR_MAP["off"], markersize=10),
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=COLOR_MAP["on"], markersize=10),
	]
	plt.legend(legend_handles, ["Load Off", "Load On"], loc="center right")
	plt.tight_layout()
	plt.savefig(output_dir / "bar-runtime.png", dpi=150)
	plt.close()


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data"
	default_output = root / "plots" / "delay-delta" / "bar"
	parser = argparse.ArgumentParser(description="Plot mean delta bars by load and runtime.")
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
	means = collect_delta_means(args.input_root, args.groups)
	plot_bar_by_load(means, output_dir)
	plot_bar_by_runtime(means, output_dir)


if __name__ == "__main__":
	main()
