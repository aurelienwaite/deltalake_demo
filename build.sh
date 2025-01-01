#/usr/bin/env bash

RUN_DIR=$(dirname $0)
pushd $RUN_DIR

cd docker/kafka
docker build -t aurelienwaite/kafka-broker:latest .
popd 
pushd $RUN_DIR
cp ./agg_pw.py docker/aggregator_kafka/
cp ./agg_kafka.py docker/aggregator_kafka/
cd docker/aggregator_kafka
docker build -t aurelienwaite/aggregator-kafka:latest .

popd
cp ./agg_pw.py docker/aggregator_redis/
cp ./agg_redis.py docker/aggregator_redis/
cd docker/aggregator_redis
docker build -t aurelienwaite/aggregator-redis:latest .
