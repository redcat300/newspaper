import redis

r = redis.Redis(
    host='redis-18272.c328.europe-west3-1.gce.redns.redis-cloud.com',
    port=18272,
    password='rNjUDWsZJvqVvBgW5Evb2zK2TahDGEfQ',
    username='default'
)


try:
    print("Connecting to Redis...")
    response = r.ping()
    if response:
        print("Connection successful:", response)
    else:
        print("Connection failed")
except Exception as e:
    print("Error:", e)
