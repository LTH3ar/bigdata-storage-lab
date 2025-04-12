# kafka_producer.py - Sends images to Kafka

from kafka import KafkaProducer
import os

KAFKA_TOPIC = "caption_topic"
KAFKA_SERVER = "kafka:9092"
IMAGE_FOLDER = "/data/images"

producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

for img_name in os.listdir(IMAGE_FOLDER):
    img_path = os.path.join(IMAGE_FOLDER, img_name)
    with open(img_path, "rb") as img_file:
        img_bytes = img_file.read()
        producer.send(KAFKA_TOPIC, key=img_name.encode(), value=img_bytes)

print("All images sent to Kafka!")
producer.close()
