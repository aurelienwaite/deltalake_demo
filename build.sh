#/usr/bin/env bash

RUN_DIR=$(dirname $0)
pushd $RUN_DIR

cd docker/kafka
docker build -t aurelienwaite/aggregator-kafka:latest .
popd 
cp ./agg_pw.py docker/aggregator/
cd docker/aggregator
docker build -t aurelienwaite/aggregator-pathways:latest .