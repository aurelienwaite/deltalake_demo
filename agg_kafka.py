import pathway as pw
from agg_pw import dataflow, AGG_TOPIC, TICK_TOPIC


rdkafka_settings = {
    "bootstrap.servers": "172.17.0.1:9092",
    "security.protocol": "plaintext",
    "group.id": "0",
    "session.timeout.ms": "6000",
    "auto.offset.reset": "earliest",
}

raw_ticks = pw.io.kafka.read(
    rdkafka_settings,
    topic=TICK_TOPIC,
    format="raw",
    autocommit_duration_ms=10,
    parallel_readers=4
)

agg_arrow = dataflow(raw_ticks)

pw.io.kafka.write(
    agg_arrow, rdkafka_settings, topic_name=AGG_TOPIC, format="raw"
)

pw.run()