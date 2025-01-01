from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from generator_protos import Producer, Consumer

BOOTSTRAP_SERVERS = "172.17.0.1:9092"

class KafkaProducer (Producer):

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
        await self.producer.start()
    
    async def send(self, topic: str, value: bytes):
        self.producer.send_and_wait(topic, value)
        
    async def stop(self):
        await self.producer.stop()
        
class KafkaConsumer (Consumer):
        
    def __init__(self, topic: str):
        self.topic = topic
    
    async def start(self):
        self.consumer = AIOKafkaConsumer(self.topic, bootstrap_servers=BOOTSTRAP_SERVERS)
        await self.consumer.start()
        
    async def __anext__(self):
        msg = await anext(self.consumer)
        return msg.value
        
    def __aiter__(self):
        return self