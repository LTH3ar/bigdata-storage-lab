import os
import pandas as pd
from kafka import KafkaProducer
import json

bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
producer = KafkaProducer(bootstrap_servers=bootstrap,
                         value_serializer=lambda v: json.dumps(v).encode())

df = pd.read_csv("/data/results.csv")
for _, r in df.iterrows():
    msg = {"image_id": r["image"], "caption": r["caption"]}
    producer.send("Captions", msg)
producer.flush()
print("Đã gửi hết caption lên Kafka")
