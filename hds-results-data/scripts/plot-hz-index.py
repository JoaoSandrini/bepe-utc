#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


COLOR_MAP = {
	"default_off": "#1f77b4",
	"default_on": "#ff7f0e",
	"kata_off": "#2ecc71",
	"kata_on": "#d62728",
}

RUNTIME_COLORS = {
	"default": "#1f77b4",
	"kata": "#ff7f0e",
}

LOAD_COLORS = {
	"off": "#1f77b4",
	"on": "#ff7f0e",
}


def read_hz_csv(csv_path: Path) -> Tuple[List[int], List[float]]:
	indices: List[int] = []
	means: List[float] = []
	with csv_path.open("r", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		for row in reader:
			indices.append(int(row["index"]))
			means.append(float(row["mean"]))
	return indices, means


def collect_series(input_root: Path, groups: List[str]) -> Dict[Tuple[str, str], Tuple[List[int], List[float]]]:
	series: Dict[Tuple[str, str], Tuple[List[int], List[float]]] = {}
	for group in groups:
		for state in ["off", "on"]:
			path = input_root / group / state / "hz" / "hz.csv"
			if not path.exists():
				continue
			series[(group, state)] = read_hz_csv(path)
	return series


def collect_hz_means(input_root: Path, groups: List[str]) -> Dict[str, Dict[str, float]]:
	means_by_group: Dict[str, Dict[str, float]] = {}
	for group in groups:
		for state in ["off", "on"]:
			path = input_root / group / state / "hz" / "hz.csv"
			if not path.exists():
				continue
			_, values = read_hz_csv(path)
			if not values:
				continue
			means_by_group.setdefault(group, {})[state] = mean(values)
	return means_by_group


def plot_hz_index_all(series: Dict[Tuple[str, str], Tuple[List[int], List[float]]], output_dir: Path) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)
	fig, ax = plt.subplots(figsize=(11, 6))
	for (group, state), (indices, means) in series.items():
		color = COLOR_MAP.get(f"{group}_{state}", "#999999")
		label = f"{group.capitalize()} {state.capitalize()}"
		ax.plot(indices, means, color=color, linewidth=1.5, label=label)

	ax.set_xlabel("Index")
	ax.set_ylabel("Message Frequency (Hz)")
	ax.set_title("Output Topic Message Frequency")
	ax.grid(True, alpha=0.3)
	ax.legend(loc="center right")
	fig.tight_layout()
	fig.savefig(output_dir / "hz-index-all.png", dpi=150)
	plt.close(fig)


def plot_hz_bar_by_load(means_by_group: Dict[str, Dict[str, float]], output_dir: Path) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)
	order: List[Tuple[str, str]] = [("default", "off"), ("kata", "off"), ("default", "on"), ("kata", "on")]
	labels = ["Off", "Off", "On", "On"]
	values: List[Optional[float]] = []
	colors: List[str] = []
	for group, state in order:
		values.append(means_by_group.get(group, {}).get(state))
		colors.append(RUNTIME_COLORS.get(group, "#999999"))

	positions = list(range(1, len(order) + 1))
	fig, ax = plt.subplots(figsize=(10, 6))
	bars = ax.bar(positions, values, color=colors, alpha=0.85, edgecolor="#000000")
	ax.set_xticks(positions, labels)
	ax.set_xlabel("Competing Load")
	ax.set_ylabel("Mean Frequency (Hz)")
	ax.set_title("Processing Frequency - Bar Plot by Load State")
	ax.grid(True, axis="y", alpha=0.3)
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
			fontweight="bold",
		)
	legend_handles = [
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=RUNTIME_COLORS["default"], markersize=10),
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=RUNTIME_COLORS["kata"], markersize=10),
	]
	ax.legend(legend_handles, ["Default Runtime", "Kata Runtime"], loc="center right")
	fig.tight_layout()
	fig.savefig(output_dir / "hz-bar-load.png", dpi=150)
	plt.close(fig)


def plot_hz_bar_by_runtime(means_by_group: Dict[str, Dict[str, float]], output_dir: Path) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)
	order: List[Tuple[str, str]] = [("default", "off"), ("default", "on"), ("kata", "off"), ("kata", "on")]
	labels = ["Default", "Default", "Kata", "Kata"]
	values: List[Optional[float]] = []
	colors: List[str] = []
	for group, state in order:
		values.append(means_by_group.get(group, {}).get(state))
		colors.append(LOAD_COLORS.get(state, "#999999"))

	positions = list(range(1, len(order) + 1))
	fig, ax = plt.subplots(figsize=(10, 6))
	bars = ax.bar(positions, values, color=colors, alpha=0.85, edgecolor="#000000")
	ax.set_xticks(positions, labels)
	ax.set_xlabel("Runtime")
	ax.set_ylabel("Mean Frequency (Hz)")
	ax.set_title("Processing Frequency - Bar Plot by Runtime")
	ax.grid(True, axis="y", alpha=0.3)
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
			fontweight="bold",
		)
	legend_handles = [
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=LOAD_COLORS["off"], markersize=10),
		plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=LOAD_COLORS["on"], markersize=10),
	]
	ax.legend(legend_handles, ["Load Off", "Load On"], loc="center right")
	fig.tight_layout()
	fig.savefig(output_dir / "hz-bar-runtime.png", dpi=150)
	plt.close(fig)


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data"
	default_output = root / "plots" / "hz"
	parser = argparse.ArgumentParser(description="Plot hz by index for all tests in a single chart.")
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
	series = collect_series(args.input_root, args.groups)
	if not series:
		raise SystemExit("No hz.csv files found to plot.")
	plot_hz_index_all(series, args.output_dir)
	means_by_group = collect_hz_means(args.input_root, args.groups)
	plot_hz_bar_by_load(means_by_group, args.output_dir)
	plot_hz_bar_by_runtime(means_by_group, args.output_dir)


if __name__ == "__main__":
	main()
