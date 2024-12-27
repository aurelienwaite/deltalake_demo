#!/bin/bash

RUN_DIR=$(dirname $0)
mkdir -p $RUN_DIR/spark_home/
chmod -R a+wx $RUN_DIR/spark_home/ 

docker run -it --rm \
    -v $RUN_DIR/spark_home:/home/spark \
    -v $RUN_DIR:/aggregator \
    -p 8888:8888 \
    -p 8080:8080 \
    -p 4040:4040 \
    -e SPARK_WORKER_DIR=/home/spark/logs \
    aurelienwaite/aggregator-toy:spark driver \
    --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,io.delta:delta-spark_2.12:3.2.0" \
    --conf "spark.driver.host=localhost" \
    --conf "spark.driver.port=8888" \
    --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp" \
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
    --conf "spark.sql.warehouse.dir=/home/spark" \
    /aggregator/aggregator.py
