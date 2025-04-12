import os, sys
from kafka import KafkaProducer
import json

bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
producer = KafkaProducer(bootstrap_servers=bootstrap,
                         value_serializer=lambda v: json.dumps(v).encode())

if len(sys.argv) < 2:
    print("Usage: python search_producer.py <query>")
    sys.exit(1)
q = sys.argv[1]
producer.send("SearchQueries", {"query": q})
producer.flush()
print(f"Đã gửi truy vấn: {q}")
