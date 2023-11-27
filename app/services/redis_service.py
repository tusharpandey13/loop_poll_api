import redis

def redis_set_status_running(redis_connection_pool, report_id):
    redis_connection = redis.Redis(connection_pool=redis_connection_pool)
    redis_connection.hset(report_id, mapping={
        "status": "Running"
    })


def redis_set_status_completed(redis_connection_pool, report_id, url):
    redis_connection = redis.Redis(connection_pool=redis_connection_pool)
    redis_connection.hset(report_id, mapping={
        "status": "Complete",
        "url": url
    })