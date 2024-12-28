# Deltalake and Latency Toy

A toy system to explore dataflow libraries. See `latency_analysis.ipynb` for a writeup.

To run locally
1. Install docker
2. `docker compose up` to start the Kafka broker and Pathways aggregator
3. Install VS Code
4. Connect to directory via start in containers
5. In a terminal in VS Code type `python tick_generator.py`

If you don't want to use VS Code then remember to change set `BOOTSTRAP_SERVERS=localhost:9092` in `tick_generator.py`

## TODO

Integrate Deltalake persistence. My plan is to have another process subscribed to the Kafka queue which listens for aggregations and saves them to the Deltalake.