from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from producer import start_kafka_producer, stop_kafka_producer, send_message
from consumer import consume_messages, stop_kafka_consumer
from Routes.modelRoutes import router as model_router
from Routes.userRoutes import router as user_router
from Routes.itemRoutes import router as item_router
from Routes.datasetRoutes import router as dataset_router
from Routes.embedding_routes import router as embedding_router
import asyncio

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await start_kafka_producer()
    asyncio.create_task(consume_messages())  # Start Kafka consumer in background

@app.on_event("shutdown")
async def shutdown_event():
    await stop_kafka_producer()
    await stop_kafka_consumer()

@app.post("message/send")
async def send_kafka_message(message: str = Body(..., embed=True)):
    await send_message("my-topic", message)
    return {"status": "Message sent", "message": message}

# Routers
app.include_router(model_router)
app.include_router(user_router)
app.include_router(item_router)
app.include_router(dataset_router)
app.include_router(embedding_router)




