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
	"kata_off": "#ff7f0e",
	"kata_on": "#ff7f0e",
}

OUTLINE_MAP = {
	"default": "#0b3d91",
	"kata": "#b34700",
	"off": "#0b3d91",
	"on": "#b34700",
}


def read_delta_series(csv_path: Path) -> List[float]:
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
			collected.setdefault(group, {})[state] = read_delta_series(path)
	return collected


def plot_violin_groups(
	collected: Dict[str, Dict[str, List[float]]],
	output_dir: Path,
	order: List[Tuple[str, str]],
	labels: List[str],
	output_name: str,
	x_label: str,
	legend_mode: str,
	color_mode: str,
) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)

	positions = [1.0 + 0.6 * idx for idx in range(len(order))]
	data: List[List[float]] = []
	colors: List[str] = []

	for group, state in order:
		series = collected.get(group, {}).get(state)
		data.append(series if series is not None else [])
		if color_mode == "load":
			colors.append(COLOR_MAP.get(f"default_{state}", "#999999"))
		elif color_mode == "runtime":
			colors.append(COLOR_MAP.get(f"{group}_off", "#999999"))
		else:
			colors.append(COLOR_MAP.get(f"{group}_{state}", "#999999"))

	plt.figure(figsize=(10, 6))
	parts = plt.violinplot(data, positions=positions, showmeans=False, showmedians=True)
	for (group, state), body, color in zip(order, parts["bodies"], colors):
		body.set_facecolor(color)
		if color_mode == "load":
			outline = OUTLINE_MAP.get(state, "#000000")
		elif color_mode == "runtime":
			outline = OUTLINE_MAP.get(group, "#000000")
		else:
			outline = OUTLINE_MAP.get(group, "#000000")
		body.set_edgecolor(outline)
		body.set_alpha(0.75)
	for key in ["cmedians", "cmins", "cmaxes", "cbars"]:
		if key in parts:
			parts[key].set_color("#000000")
			parts[key].set_linewidth(1.2)

	plt.xticks(positions, labels)
	plt.xlabel(x_label)
	plt.ylabel("Processing Time (s)")
	if output_name == "violin-runtime.png":
		plt.title("Topic Delay Delta - Violin Plot by Runtime")
	else:
		plt.title("Topic Delay Delta - Violin Plot by Load State")
	plt.grid(True, alpha=0.3)

	legend_labels = []
	legend_colors = []
	if legend_mode == "load":
		legend_labels = ["Load Off", "Load On"]
		legend_colors = [COLOR_MAP["default_off"], COLOR_MAP["default_on"]]
	else:
		legend_labels = ["Default Runtime", "Kata Runtime"]
		legend_colors = [COLOR_MAP["default_off"], COLOR_MAP["kata_off"]]

	legend_handles = [
		plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=color, markersize=8)
		for color in legend_colors
	]
	plt.legend(legend_handles, legend_labels, loc="center right")
	plt.tight_layout()
	plt.savefig(output_dir / output_name, dpi=150)
	plt.close()


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data"
	default_output = root / "plots" / "delay-delta" / "violin"
	parser = argparse.ArgumentParser(
		description="Plot delta violin plots with load/runtime ordering."
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
	plot_violin_groups(
		collected,
		args.output_dir,
		order=[("default", "off"), ("kata", "off"), ("default", "on"), ("kata", "on")],
		labels=["Off", "Off", "On", "On"],
		output_name="violin-load.png",
		x_label="Competing Load",
		legend_mode="group",
		color_mode="runtime",
	)
	plot_violin_groups(
		collected,
		args.output_dir,
		order=[("default", "off"), ("default", "on"), ("kata", "off"), ("kata", "on")],
		labels=["Default", "Default", "Kata", "Kata"],
		output_name="violin-runtime.png",
		x_label="Runtime",
		legend_mode="load",
		color_mode="load",
	)


if __name__ == "__main__":
	main()
