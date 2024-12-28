# Test script that creates synthetic ticks to be aggregated

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import random
from datetime import datetime, timezone
import polars as pl
import pyarrow as pa
from dataclasses import dataclass, fields
from typing import Sequence
from json import dumps

symbols = ["a", "b", "c", "d", "e"]
num_files = 10000
BOOTSTRAP_SERVERS = "172.17.0.1:9092"

@dataclass
class Aggregation:
    symbol: str
    start: datetime
    end: datetime
    sum: float
    count: float

def parse_arrow(binary_message: bytes) -> Sequence[Aggregation]:
    reader = pa.ipc.open_stream(binary_message)
    table = reader.read_all()
    columns = [table[column] for column in [f.name for f in fields(Aggregation)]]
    aggs = []
    for row_idx in range(table.num_rows):
        agg = Aggregation(*[column[row_idx].as_py() for column in columns])
        aggs.append(agg)
    return aggs

async def generate_ticks():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()
    for i in range(num_files):
        await asyncio.sleep(0.01)
        if random.randint(0,9) == 0:
            num_ticks_per_file = 10
            ticks = []
            for _ in range(num_ticks_per_file):
                tick = {
                    "symbol": random.choice(symbols),
                    "timestamp": datetime.now(tz=timezone.utc),
                    "price": round(random.uniform(100, 1500), 2)
                }
                ticks.append(tick)
            df = pl.DataFrame(data=ticks, schema={"symbol": pl.String, "timestamp": pl.Datetime, "price": pl.Float64})
            table = df.to_arrow()
            sink = pa.BufferOutputStream()
            with pa.ipc.new_stream(sink, table.schema) as writer:
                writer.write_table(table)
            buffer = sink.getvalue()
            await producer.send_and_wait("tick", buffer.to_pybytes())
    await producer.stop()
    print("Finished generating ticks")
    
latency_data_file = open("./latency.ndjson", "w")

async def consume_aggregations():
    consumer = AIOKafkaConsumer("aggregation", bootstrap_servers=BOOTSTRAP_SERVERS)
    await consumer.start()
    async for msg in consumer:
        for agg in parse_arrow(msg.value):
            now = datetime.now(tz=timezone.utc)
            end = agg.end
            diff = (now - end).total_seconds() * 1000
            print(f"Received update for symbol \"{agg.symbol}\" and window end {end}: sum={agg.sum} count={agg.count} (delay={diff}ms)")
            datum = {"symbol": agg.symbol, "delay": diff, "window_end": end.isoformat(), "sum": agg.sum, "count": agg.count}
            latency_data_file.write(dumps(datum) + "\n")
            

async def produce_consume():
    await asyncio.gather(generate_ticks(), consume_aggregations())

asyncio.run(produce_consume())