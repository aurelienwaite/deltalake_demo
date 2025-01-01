import pathway as pw
from agg_pw import dataflow, AGG_TOPIC, TICK_TOPIC
from pathway.io.python import ConnectorSubject
import redis.asyncio as async_redis
import redis
import asyncio

async_redis = async_redis.from_url("redis://172.17.0.1")
redis = redis.from_url("redis://172.17.0.1")
pubsub = async_redis.pubsub()

class RedisSchema(pw.Schema):
    data: bytes

class RedisSubject(ConnectorSubject):
    
    def run(self) -> None:
        async def async_message_loop():
            await pubsub.subscribe(TICK_TOPIC)
            while True:
                msg = await pubsub.get_message(ignore_subscribe_messages=True)
                if msg is not None:
                    self.next(data=msg["data"])
        
        asyncio.run(async_message_loop())
        
        
    @property
    def _deletions_enabled(self) -> bool:
        return False

s = RedisSubject()
table = pw.io.python.read(s, schema=RedisSchema)

agg_table = dataflow(table)

def on_change(key: pw.Pointer, row: dict, time: int, is_addition: bool):
    msg: bytes = row["data"]
    redis.publish(AGG_TOPIC, msg)

pw.io.subscribe(agg_table, on_change)

pw.run()