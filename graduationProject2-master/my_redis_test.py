# redis_client.py
import redis

r = redis.Redis(
    host='redis-10187.c228.us-central1-1.gce.redns.redis-cloud.com',
    port=10187,
    decode_responses=True,
    username="default",
    password="z5YF6AkEmV7Ousk3iyzPMkRx0PwAxcTa",
)
    