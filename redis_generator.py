import redis.asyncio as redis
from generator_protos import Producer, Consumer

redis = redis.from_url("redis://172.17.0.1")
pubsub = redis.pubsub()

class RedisProducer(Producer):
    
    async def start(self):
        pass
        
    async def send(self, topic: str, value: bytes):
        await redis.publish(topic, value)

    async def stop(self):
        pass
    
class RedisConsumer(Consumer):
    
    def __init__(self, topic: str):
        self.topic = topic

    async def start(self):
        await pubsub.subscribe(self.topic)

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None:
                return message["data"]

    async def stop(self):
        await pubsub.close()
