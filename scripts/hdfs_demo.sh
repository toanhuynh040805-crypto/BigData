#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose -f infra/hdfs/compose.yaml up -d namenode datanode1 datanode2
ready=0
report=""
for attempt in $(seq 1 50); do
  # Capture whole output first: grep -q with pipefail could falsely fail via SIGPIPE.
  report="$(docker compose -f infra/hdfs/compose.yaml exec -T namenode hdfs dfsadmin -report 2>&1 || true)"
  if [[ "$report" == *"Live datanodes (2)"* ]]; then
    ready=1
    break
  fi
  if (( attempt % 10 == 0 )); then
    printf 'HDFS check %s: %s\n' "$attempt" "$(echo "$report" | grep -m1 'Live datanodes' || echo 'waiting for HDFS')"
  fi
  sleep 3
done
if [ "$ready" != "1" ]; then
  docker compose -f infra/hdfs/compose.yaml ps
  printf '%s\n' "$report" | tail -n 35
  echo "HDFS did not report 2 live DataNodes" >&2
  exit 1
fi
docker compose -f infra/hdfs/compose.yaml exec -T namenode hdfs dfsadmin -report | grep "Live datanodes"
if [ ! -f data/sample/household_power_consumption.txt ]; then
  python scripts/generate_sample.py --days 15
fi
docker compose -f infra/hdfs/compose.yaml cp data/sample/household_power_consumption.txt namenode:/tmp/sample_energy.txt
docker compose -f infra/hdfs/compose.yaml exec -T namenode hdfs dfs -mkdir -p /bigdata/energy/raw
docker compose -f infra/hdfs/compose.yaml exec -T namenode hdfs dfs -put -f /tmp/sample_energy.txt /bigdata/energy/raw/household_power_consumption.txt
docker compose -f infra/hdfs/compose.yaml exec -T namenode hdfs dfs -ls /bigdata/energy/raw/
echo "Sample dataset stored on distributed HDFS."
