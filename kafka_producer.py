from kafka import KafkaProducer
import os
import json

KAFKA_TOPIC_IMAGE = "image_topic"
KAFKA_TOPIC_CAPTION = "caption_topic"
KAFKA_SERVER = "kafka:9092"
IMAGE_FOLDER = "/data/images"
CAPTIONS_FILE = "/data/results.csv"

producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

# Đọc dữ liệu caption từ file CSV
captions = []
with open(CAPTIONS_FILE, 'r') as f:
    for line in f.readlines():
        parts = line.strip().split(',')
        captions.append({"image": parts[0], "caption": parts[1]})

# Gửi ảnh và caption vào Kafka
for img_name in os.listdir(IMAGE_FOLDER):
    img_path = os.path.join(IMAGE_FOLDER, img_name)
    with open(img_path, "rb") as img_file:
        img_bytes = img_file.read()
        producer.send(KAFKA_TOPIC_IMAGE, key=img_name.encode(), value=img_bytes)

        # Gửi caption
        for caption in captions:
            if caption['image'] == img_name:
                producer.send(KAFKA_TOPIC_CAPTION, value=json.dumps(caption).encode())

print("Tất cả ảnh và caption đã được gửi vào Kafka!")
producer.close()

