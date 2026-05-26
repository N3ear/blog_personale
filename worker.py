import os

import redis
from rq import Connection, Worker


def build_redis_connection():
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis.from_url(redis_url)

    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    return redis.Redis(host=redis_host, port=redis_port, db=redis_db)


listen = ["default"]
redis_connection = build_redis_connection()


if __name__ == "__main__":
    with Connection(redis_connection):
        worker = Worker(listen)
        worker.work()
