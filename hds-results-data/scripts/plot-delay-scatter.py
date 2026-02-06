#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import random


COLOR_MAP = {
	"default_off": "#1f77b4",
	"default_on": "#ff7f0e",
	"kata_off": "#ff7f0e",
	"kata_on": "#ff7f0e",
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


def collect_delta_series(input_root: Path, groups: List[str]) -> Dict[str, Dict[str, Tuple[List[int], List[float]]]]:
	collected: Dict[str, Dict[str, Tuple[List[int], List[float]]]] = {}
	for group in groups:
		group_root = input_root / group
		for state in ["off", "on"]:
			path = group_root / state / "delays" / "delta.csv"
			if not path.exists():
				continue
			collected.setdefault(group, {})[state] = read_delta_series(path)
	return collected


def jitter(value: float, amount: float) -> float:
	return value + random.uniform(-amount, amount)


def plot_scatter_groups(
	collected: Dict[str, Dict[str, Tuple[List[int], List[float]]]],
	output_dir: Path,
	jitter_amount: float,
	order: List[Tuple[str, str]],
	labels: List[str],
	output_name: str,
	x_label: str,
	legend_mode: str,
	color_mode: str,
) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)

	positions = [1.0 + 0.6 * idx for idx in range(len(order))]

	plt.figure(figsize=(10, 6))
	seen_states = set()
	seen_groups = set()
	for (group, state), pos in zip(order, positions):
		series = collected.get(group, {}).get(state)
		if not series:
			continue
		_, ys = series
		xs_jitter = [jitter(float(pos), jitter_amount) for _ in ys]
		if legend_mode == "load":
			label = f"Load {state.capitalize()}"
			if state in seen_states:
				label = "_nolegend_"
			else:
				seen_states.add(state)
		else:
			label = f"{group.capitalize()} {state.capitalize()}"
			if legend_mode == "group":
				label = "Default Runtime" if group == "default" else "Kata Runtime"
				if group in seen_groups:
					label = "_nolegend_"
				else:
					seen_groups.add(group)
		if color_mode == "load":
			color = COLOR_MAP.get(f"default_{state}")
		elif color_mode == "runtime":
			color = COLOR_MAP.get(f"{group}_off")
		else:
			color = COLOR_MAP.get(f"{group}_{state}")
		plt.scatter(
			xs_jitter,
			ys,
			label=label,
			alpha=0.7,
			s=12,
			color=color,
		)
	plt.xticks(positions, labels)
	plt.xlabel(x_label)
	plt.ylabel("Processing Time (s)")
	if output_name == "scatter-runtime.png":
		plt.title("Topic Delay Delta (/perceptions - /points) - Scatter Plot by Runtime")
	else:
		plt.title("Topic Delay Delta (/perceptions - /points) - Scatter Plot by Load State")
	plt.grid(True, alpha=0.3)
	plt.legend(loc="center right", markerscale=1.6)
	plt.tight_layout()
	plt.savefig(output_dir / output_name, dpi=150)
	plt.close()


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data"
	default_output = root / "plots" / "delay-delta" / "scatter"
	parser = argparse.ArgumentParser(
		description="Plot delta scatterplots with horizontal jitter."
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
	parser.add_argument(
		"--jitter",
		type=float,
		default=0.2,
		help="Horizontal jitter amount.",
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=42,
		help="Random seed for jitter.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	random.seed(args.seed)
	collected = collect_delta_series(args.input_root, args.groups)
	plot_scatter_groups(
		collected,
		args.output_dir,
		args.jitter,
		order=[("default", "off"), ("kata", "off"), ("default", "on"), ("kata", "on")],
		labels=["Off", "Off", "On", "On"],
		output_name="scatter-load.png",
		x_label="Competing Load",
		legend_mode="group",
		color_mode="runtime",
	)
	plot_scatter_groups(
		collected,
		args.output_dir,
		args.jitter,
		order=[("default", "off"), ("default", "on"), ("kata", "off"), ("kata", "on")],
		labels=["Default", "Default", "Kata", "Kata"],
		output_name="scatter-runtime.png",
		x_label="Runtime",
		legend_mode="load",
		color_mode="load",
	)


if __name__ == "__main__":
	main()
