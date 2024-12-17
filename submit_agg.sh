#!/bin/bash

RUN_DIR=`dirname $0`
mkdir -p $RUN_DIR/spark_home

docker run -it --rm -v $RUN_DIR/spark_home:/home/spark -v $RUN_DIR:/aggregator -p 8888:8888 -p 8080:8080 -p 4040:4040 spark:python3-java17 driver --conf "spark.driver.host=localhost" --conf "spark.driver.port=8888" --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp" --packages io.delta:delta-spark_2.12:3.2.0 --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" /aggregator/aggregator.py