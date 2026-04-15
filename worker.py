import os

import redis
from rq import Connection, Queue, Worker


listen = ["default"]
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def main():
    conn = redis.from_url(redis_url, decode_responses=False)
    with Connection(conn):
        worker = Worker([Queue(name) for name in listen])
        worker.work()


if __name__ == "__main__":
    main()
