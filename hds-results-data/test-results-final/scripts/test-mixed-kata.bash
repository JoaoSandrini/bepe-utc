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

for i in $(seq 1 10); do
    printf "Starting on test iteration $i timestamp %s\n" "$(date +%s)" >> /home/hds/test-results-final/mixed/kata/timestamps/timestamps.txt

    ros2 topic delay --window 10 /points > /home/hds/test-results-final/mixed/kata/delays/points-kata-on-$i.txt &
    PIDS+=($!)

    ros2 topic delay --window 10 /perceptions > /home/hds/test-results-final/mixed/kata/delays/perceptions-kata-on-$i.txt &
    PIDS+=($!)
    
    ros2 topic hz /perceptions > /home/hds/test-results-final/mixed/kata/hz/hz-$i.txt &
    PIDS+=($!)

    ros2 bag play /home/hds/hds-datasets/live-test/rosbag2_2026_01_26-16_45_14_0.mcap --exclude-topics /perceptions --clock

    cleanup
    sleep 1
    printf "Ending on test iteration $i timestamp %s\n\n" "$(date +%s)" >> /home/hds/test-results-final/mixed/kata/timestamps/timestamps.txt
done
