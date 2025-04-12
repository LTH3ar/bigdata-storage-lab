# kafka_producer.py - Sends images to Kafka

from kafka import KafkaProducer
import os
import sys
import pandas as pd

KAFKA_TOPIC = "image_topic"
KAFKA_SERVER = "kafka:9092"
IMAGE_FOLDER = "/data/images"

# csv
# image metadata csv file
csv_file = '/data/images/Folds.csv'

# Read CSV file
df = pd.read_csv(csv_file)
# Filter for train (column: grp)
df_train = df[df['grp'] == 'train']
# Get image paths and labels:
"""
columns: filename
BreaKHis_v1/histology_slides/breast/benign/SOB/adenosis/SOB_B_A_14-22549AB/100X/SOB_B_A-14-22549AB-100-001.png

can use the filename column to get the benign/malignant label
"""


producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

# for img_name in os.listdir(IMAGE_FOLDER):
#     img_path = os.path.join(IMAGE_FOLDER, img_name)
#     with open(img_path, "rb") as img_file:
#         img_bytes = img_file.read()
#         producer.send(KAFKA_TOPIC, key=img_name.encode(), value=img_bytes)

for index, row in df_train.iterrows():
    # Get the image path and label
    filename = row['filename']
    label = filename.split('/')[3]  # benign/malignant
    img_path = os.path.join(IMAGE_FOLDER, filename)
    
    # Read the image and encode it to base64
    with open(img_path, 'rb') as f:
        img_bytes = f.read()
    
    # Send the message to Kafka
    producer.send(KAFKA_TOPIC, key=filename.encode(), value=img_bytes)
    producer.flush()
    print(f"Sent image {os.path.basename(img_path)} with label {label}")

print("All images sent to Kafka!")
producer.close()
