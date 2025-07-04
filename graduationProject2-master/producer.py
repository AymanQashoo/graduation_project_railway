from aiokafka import AIOKafkaProducer

producer = None

async def start_kafka_producer():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await producer.start()
    print("[Kafka Producer] Started")

async def stop_kafka_producer():
    if producer:
        await producer.stop()
        print("[Kafka Producer] Stopped")

async def send_message(topic: str, message: str):
    if producer:
        await producer.send_and_wait(topic, message.encode("utf-8"))
        print(f"[Kafka Producer] Sent: {message}")
