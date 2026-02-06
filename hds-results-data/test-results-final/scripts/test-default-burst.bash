#!/bin/bash
set -e

export RMW_IMPLEMENTATION=rmw_zenoh_cpp
source /WS/install/setup.bash

PIDS=()

cleanup() {
    echo "Cleaning up ros2 topic delay..."
    for pid in "${PIDS[@]}"; do
        kill -INT "$pid" 2>/dev/null || true
    done
    sleep 1
    PIDS=()
}
trap cleanup EXIT

printf "%s\n" "$(date +%s)" >> /home/hds/test-results-final/default/burst/timestamps/timestamps.txt

ros2 topic delay --window 10 /points > /home/hds/test-results-final/default/burst/delays/points.txt &
PIDS+=($!)

ros2 topic delay --window 10 /perceptions > /home/hds/test-results-final/default/burst/delays/perceptions.txt &
PIDS+=($!)

ros2 topic hz /perceptions > /home/hds/test-results-final/default/burst/hz/hz.txt &
PIDS+=($!)

ros2 bag play /home/hds/hds-datasets/live-test/rosbag2_2026_01_26-16_45_14_0.mcap --exclude-topics /perceptions --clock &
bagpid=$!

sleep 113
echo run load!

wait $bagpid
cleanup
sleep 1
printf "%s" "$(date +%s)" >> /home/hds/test-results-final/default/burst/timestamps/timestamps.txt
