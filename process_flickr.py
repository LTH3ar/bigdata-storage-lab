from kafka import KafkaProducer, KafkaConsumer
import json
import os

KAFKA_BROKER = "kafka:9092"
TOPIC = "flickr_images"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# Load Flickr30k image names from local storage
images_dir = "/data/images"
image_list = os.listdir(images_dir)

# Send image metadata to Kafka
for image in image_list:
    metadata = {"image": image, "path": f"/data/images/{image}"}
    producer.send(TOPIC, metadata)

producer.flush()
print("Sent image metadata to Kafka.")

# Kafka Consumer (for Spark processing)
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset="earliest",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

print("Waiting for messages...")
for message in consumer:
    print(f"Processing: {message.value}")
    # Here, Spark processing logic should be implemented.
