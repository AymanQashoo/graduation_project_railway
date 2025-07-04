from aiokafka import AIOKafkaConsumer

consumer = None

async def consume_messages():
    global consumer
    print("[Kafka Consumer] Starting...")

    consumer = AIOKafkaConsumer(
        "my-topic",
        bootstrap_servers="localhost:9092",
        group_id="my-group",
        auto_offset_reset="latest",
    )
    await consumer.start()
    print("[Kafka Consumer] Started!")

    try:
        async for msg in consumer:
            print(f"[Kafka Consumer] Received: {msg.value.decode('utf-8')}")
    except Exception as e:
        print("[Kafka Consumer] Error:", e)
    finally:
        await consumer.stop()
        print("[Kafka Consumer] Stopped")

async def stop_kafka_consumer():
    if consumer:
        await consumer.stop()
        print("[Kafka Consumer] Stopped")
