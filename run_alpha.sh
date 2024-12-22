#!/bin/bash

RUN_DIR=$(dirname $0)

docker run -it --rm \
    -v $RUN_DIR:/aggregator \
    -p 8815:8815 \
    aurelienwaite/aggregator-toy:alpha \
    python /aggregator/alpha_example.py