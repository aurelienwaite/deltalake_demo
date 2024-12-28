#!/usr/bin/env bash
set -m

/etc/kafka/docker/run &

while ! nc -z 172.17.0.1 9092; do
  echo "Waiting for Kafka to start..."
  sleep 1
done

echo "Creating Kafka topics"
/opt/kafka/bin/kafka-topics.sh --bootstrap-server 172.17.0.1:9092 --create --topic tick
/opt/kafka/bin/kafka-topics.sh --bootstrap-server 172.17.0.1:9092 --create --topic aggregation

fg %1