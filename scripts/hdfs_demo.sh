#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose -f infra/hdfs/compose.yaml up -d namenode datanode1 datanode2
ready=0
for attempt in $(seq 1 60); do
  if docker compose -f infra/hdfs/compose.yaml exec -T namenode hdfs dfsadmin -report 2>/dev/null | grep -q 'Live datanodes (2)'; then
    ready=1
    break
  fi
  sleep 4
done
if [ "$ready" != "1" ]; then
  docker compose -f infra/hdfs/compose.yaml ps
  echo "HDFS cluster failed to register 2 DataNodes" >&2
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
