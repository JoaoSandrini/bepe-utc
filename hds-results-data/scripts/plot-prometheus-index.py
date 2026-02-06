#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


RUNTIME_COLORS = {
	"default": "#1f77b4",
	"kata": "#ff7f0e",
}

LOAD_COLOR = "#2ecc71"


def read_mean_series(csv_path: Path) -> Tuple[List[int], List[float]]:
	indices: List[int] = []
	values: List[float] = []
	with csv_path.open("r", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		for row in reader:
			indices.append(int(row["index"]))
			values.append(float(row["mean"]))
	return indices, values


def load_runtime_series(
	input_root: Path,
	group: str,
	state: str,
) -> Dict[str, Tuple[List[int], List[float]]]:
	series: Dict[str, Tuple[List[int], List[float]]] = {}
	cpu_path = input_root / group / state / "prometheus" / "cpu" / "mean.csv"
	mem_path = input_root / group / state / "prometheus" / "mem" / "mean.csv"
	if cpu_path.exists():
		series["cpu"] = read_mean_series(cpu_path)
	if mem_path.exists():
		series["mem"] = read_mean_series(mem_path)
	return series


def load_stressor_series(input_root: Path, group: str) -> Dict[str, Tuple[List[int], List[float]]]:
	series: Dict[str, Tuple[List[int], List[float]]] = {}
	cpu_path = input_root / group / "on" / "prometheus" / "cpu-stressor" / "mean.csv"
	mem_path = input_root / group / "on" / "prometheus" / "mem-stressor" / "mean.csv"
	if cpu_path.exists():
		series["cpu"] = read_mean_series(cpu_path)
	if mem_path.exists():
		series["mem"] = read_mean_series(mem_path)
	return series


def pick_stressor_series(input_root: Path, groups: List[str]) -> Optional[Dict[str, Tuple[List[int], List[float]]]]:
	for group in groups:
		series = load_stressor_series(input_root, group)
		if series:
			return series
	return None


def to_percent(values: List[float], metric: str, total_cpu_cores: float, total_ram_bytes: float) -> List[float]:
	if metric == "cpu":
		return [(value / total_cpu_cores) * 100 for value in values]
	if metric == "mem":
		return [(value / total_ram_bytes) * 100 for value in values]
	return values


def plot_prometheus_state(
	input_root: Path,
	groups: List[str],
	state: str,
	total_cpu_cores: float,
	total_ram_bytes: float,
	output_dir: Path,
) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)
	fig, ax = plt.subplots(figsize=(11, 6))

	for group in groups:
		series = load_runtime_series(input_root, group, state)
		color = RUNTIME_COLORS.get(group, "#333333")
		if "cpu" in series:
			xs, ys = series["cpu"]
			ax.plot(
				xs,
				to_percent(ys, "cpu", total_cpu_cores, total_ram_bytes),
				color=color,
				linewidth=1.6,
				linestyle="-",
				label=f"{group.capitalize()} CPU",
			)
		if "mem" in series:
			xs, ys = series["mem"]
			ax.plot(
				xs,
				to_percent(ys, "mem", total_cpu_cores, total_ram_bytes),
				color=color,
				linewidth=1.6,
				linestyle="--",
				label=f"{group.capitalize()} Memory",
			)

	if state == "on":
		stressor_series = pick_stressor_series(input_root, groups)
		if stressor_series:
			if "cpu" in stressor_series:
				xs, ys = stressor_series["cpu"]
				ax.plot(
					xs,
					to_percent(ys, "cpu", total_cpu_cores, total_ram_bytes),
					color=LOAD_COLOR,
					linewidth=1.6,
					linestyle="-",
					label="Load CPU",
				)
			if "mem" in stressor_series:
				xs, ys = stressor_series["mem"]
				ax.plot(
					xs,
					to_percent(ys, "mem", total_cpu_cores, total_ram_bytes),
					color=LOAD_COLOR,
					linewidth=1.6,
					linestyle="--",
					label="Load Memory",
				)

	ax.set_xlabel("Measurement Index")
	ax.set_ylabel("Usage (%)")
	ax.set_title(f"Prometheus CPU and Memory Usage - Load {state.capitalize()}")
	ax.grid(True, alpha=0.3)
	ax.legend(loc="center right")
	fig.tight_layout()
	fig.savefig(output_dir / f"prometheus-{state}.png", dpi=150)
	plt.close(fig)


def parse_args() -> argparse.Namespace:
	root = Path(__file__).resolve().parents[1]
	default_input = root / "treated-data"
	default_output = root / "plots" / "prometheus"
	parser = argparse.ArgumentParser(description="Plot Prometheus CPU and memory usage for off/on.")
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
		"--cpu-cores",
		type=float,
		default=10,
		help="Total CPU cores to normalize usage to percentage.",
	)
	parser.add_argument(
		"--ram-gb",
		type=float,
		default=64,
		help="Total RAM in GB to normalize usage to percentage.",
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
	total_ram_bytes = args.ram_gb * 1024 * 1024 * 1024
	plot_prometheus_state(args.input_root, args.groups, "off", args.cpu_cores, total_ram_bytes, args.output_dir)
	plot_prometheus_state(args.input_root, args.groups, "on", args.cpu_cores, total_ram_bytes, args.output_dir)


if __name__ == "__main__":
	main()
