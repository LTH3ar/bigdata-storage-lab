# spark_kafka_hdfs.py - Spark job to consume Kafka stream and save to HDFS
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import BinaryType

"""
this script is to respond to the kafka producer
filename = row['filename']
label = filename.split('/')[3]  # benign/malignant
img_path = os.path.join(IMAGE_FOLDER, filename)

# Read the image and encode it to base64
with open(img_path, 'rb') as f:
    img_bytes = f.read()

# Send the message to Kafka
producer.send(KAFKA_TOPIC, key=filename.encode(), value=img_bytes)
"""

# import neccessary libraries for image processing
from PIL import Image
import io
import numpy as np

# Define a UDF for processing image data
@udf(returnType=BinaryType())
def process_image_data_udf(image_data):
    # Convert binary data to image
    image = Image.open(io.BytesIO(image_data))
    # Resize image to 224x224
    image = image.resize((224, 224))
    # Convert image to numpy array
    image_array = np.array(image)
    # Normalize image data
    image_array = image_array / 255.0
    # Convert back to binary
    image = Image.fromarray((image_array * 255).astype(np.uint8))
    byte_io = io.BytesIO()
    image.save(byte_io, format='PNG')
    byte_io.seek(0)
    return byte_io.read()

KAFKA_TOPIC = "image_topic"
KAFKA_SERVER = "kafka:9092"
#HDFS_OUTPUT_PATH_RAW = "hdfs://namenode:9000/raw_images/"
HDFS_OUTPUT_PATH_PROCESSED = "hdfs://namenode:9000/processed_images/"

spark = SparkSession.builder.appName("KafkaToHDFS").getOrCreate()

# Read stream from Kafka and get the image data
query = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_SERVER)
    .option("subscribe", KAFKA_TOPIC)
    .load()
)
# Process the image data
processed_images = (
    query.selectExpr("CAST(key AS STRING)", "CAST(value AS BINARY) as image_data")
    .withColumn("image_data", process_image_data_udf(col("image_data")))
)
# Write the processed images to HDFS
query = (
    processed_images.writeStream
    .outputMode("append")
    .format("parquet")
    .option("path", HDFS_OUTPUT_PATH_PROCESSED)
    .option("checkpointLocation", "/tmp/kafka_to_hdfs_checkpoint")
    .start()
)

query.awaitTermination()
